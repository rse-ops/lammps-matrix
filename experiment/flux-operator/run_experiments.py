#!/usr/bin/env python3

import argparse
import copy
import json
import multiprocessing
import os
import subprocess
import shutil
import random
import sys
import tempfile
import yaml
from collections import defaultdict
from datetime import datetime

from jinja2 import Template
from kubernetes import client, config, watch

here = os.path.dirname(os.path.abspath(__file__))

# Hard coded experiment templates
lammps_template = os.path.join(here, "crd", "lammps.yaml")

six_config = [
    {"x": 2, "y": 2, "z": 2, "cpu_limit": 2, "tasks": 4, "size": 2},
]

# We are matching os version exactly - in the future we can specify a range, etc.
# Arguably this could come from matching specs across containers, but for bare metal we would
# extract from the host directly.
rocky_9 = {
    "org.supercontainers.os.vendor": "rocky",
    "org.supercontainers.os.version": "9.3",
}
rocky_8 = {
    "org.supercontainers.os.vendor": "rocky",
    "org.supercontainers.os.version": "8.9",
}
ubuntu_2004 = {
    "org.supercontainers.os.vendor": "ubuntu",
    "org.supercontainers.os.version": "20.04",
}
ubuntu_2204 = {
    "org.supercontainers.os.vendor": "ubuntu",
    "org.supercontainers.os.version": "22.04",
}

rocky_views = [
    "ghcr.io/converged-computing/flux-view-rocky:tag-8",
    "ghcr.io/converged-computing/flux-view-rocky:tag-9",
]

ubuntu_views = [
    "ghcr.io/converged-computing/flux-view-ubuntu:tag-focal",
    "ghcr.io/converged-computing/flux-view-ubuntu:tag-jammy",
]

# These are matches we will request for each platform and flux view
req = {
    "amd64": [
        {
            "image": "ghcr.io/converged-computing/flux-view-rocky:tag-9",
            "match": rocky_9,
        },
        {
            "image": "ghcr.io/converged-computing/flux-view-rocky:tag-8",
            "match": rocky_8,
        },
        {
            "image": "ghcr.io/converged-computing/flux-view-ubuntu:tag-focal",
            "match": ubuntu_2004,
        },
        {
            "image": "ghcr.io/converged-computing/flux-view-ubuntu:tag-jammy",
            "match": ubuntu_2204,
        },
    ],
    "arm64": [
        {
            "image": "ghcr.io/converged-computing/flux-view-rocky:arm-9",
            "match": rocky_9,
        },
        {
            "image": "ghcr.io/converged-computing/flux-view-rocky:arm-8",
            "match": rocky_8,
        },
        {
            "image": "ghcr.io/converged-computing/flux-view-ubuntu:arm-focal",
            "match": ubuntu_2004,
        },
        {
            "image": "ghcr.io/converged-computing/flux-view-ubuntu:arm-jammy",
            "match": ubuntu_2204,
        },
    ],
}


# Pair up configs and named templates
configs = {
    "lammps-six": {"config": six_config, "template": lammps_template},
}

# This must work to continue
config.load_kube_config()
kube_client = client.CoreV1Api()

# Try using a global watcher
watcher = watch.Watch()


def write_file(content, filename):
    """
    Write content to file.
    """
    with open(filename, "w") as fd:
        fd.write(content)


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def load_yaml(filename):
    """
    Read yaml from file.
    """
    with open(filename, "r") as stream:
        content = yaml.safe_load(stream)
    return content


def save_nodes(logfile):
    """
    Save node configuration.
    """
    cluster_nodes = kube_client.list_node()
    nodes = cluster_nodes.to_str()
    write_file(nodes, logfile)


def submit_job(minicluster_yaml):
    """
    Create the job in Kubernetes.
    """
    fd, filename = tempfile.mkstemp(suffix=".yaml", prefix="minicluster-")
    os.remove(filename)
    os.close(fd)
    write_file(minicluster_yaml, filename)

    # Create the minicluster
    o, e = run_command(["kubectl", "apply", "-f", filename])
    os.remove(filename)


def run_command(command, quiet=False):
    """
    Call a command to subprocess, return output and error.
    """
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    o, e = p.communicate()
    if not quiet:
        print(o)
    if p.returncode:
        print(e)
        raise RuntimeError(e)
    return o, e


def delete_minicluster(uid):
    """
    Delete the Minicluster, which includes an indexed job,
    config maps, and service.
    """
    # --wait=true is default, but I want to be explicit
    run_command(
        ["kubectl", "delete", "miniclusters.flux-framework.org", uid, "--wait=true"]
    )


def record_line(filename, status, content):
    """
    Record (write with append) one entry to a file.
    """
    with open(filename, "a") as f:
        f.write(f"\n===\n{status}: recorded-at: {datetime.utcnow()}\n{content}")


def show_logs(name):
    """
    Show lines from the log.

    This will error when the pod isn't ready yet.
    """
    lines = []
    for line in watcher.stream(
        kube_client.read_namespaced_pod_log,
        name=name,
        namespace="default",
    ):
        lines.append(line)
    return "\n".join(lines)


def get_logs(uid, meta, start_time, log_dir):
    """
    Get the application mapping and performance logs
    """
    log_file = os.path.join(log_dir, f"{uid}.log")

    # Find pods for minicluster
    label = meta["params"]["name"]

    # Wait for pods
    # Wait for the leader pod to be running before listing
    while True:
        pods = kube_client.list_namespaced_pod(
            label_selector=f"app={label}", namespace="default"
        )
        # Phases here:
        phases = [x.status.phase for x in pods.items]
        is_running = all([p in ["Running", "Succeeded", "Failed"] for p in phases])
        if len(pods.items) == meta["params"]["size"] and is_running:
            break

    # And then the 0th index (leader) and the rest are workers (not used here)
    zero_index = f"{label}-0"
    leader = [x for x in pods.items if x.metadata.name.startswith(zero_index)][0]
    print(f"Found minicluster leader pod {leader.metadata.name} to watch 👀️")

    # Stream log until it completes (and we will get events after)
    print(f"Waiting to get log for {uid} from pod {leader.metadata.name}")
    while True:
        try:
            log = show_logs(leader.metadata.name)

            # If we hit the point where it's running but no logs...
            if not log:
                continue
            break
        except:
            continue

    # Save the log file
    write_file(log, log_file)


def organize_manifests(manifests):
    """
    Organize manifests based on platform, which is what we ultimately care about.
    The actual image selection for the descriptive case will be done by compspec.
    """
    organized = {"arm64": [], "amd64": []}
    if "images" not in manifests:
        sys.exit('Expected to find "images" key in manifests list.')

    for image in manifests["images"]:
        if "arm" in image["name"]:
            organized["arm64"].append(image)
        else:
            organized["amd64"].append(image)
    return organized


def generate_basic_minicluster(args, manifests, cfg, name):
    """
    Generate a platform based experiment, meaning we consider the platform

    For the basic setup, we only care about platform. We know nothing else
    about the compatibility so randomly select all with matching platform.
    We can just derive this from the image name/uri, normally for image
    selection it would come from the registry platform section of the
    manifest.
    """
    # For basic platform, we hard code a single os to be consistent
    container = "ghcr.io/converged-computing/flux-view-ubuntu:tag-jammy"
    render = generate_basic_base(args, manifests, cfg, name)
    render["flux_container"] = container
    return render


def generate_platform_minicluster(args, manifests, cfg, name):
    """
    For the platform minicluster we select the view based on ubuntu or
    rocky, and randomly.
    """
    render = generate_basic_base(args, manifests, cfg, name)
    if "ubuntu" in render["image"]:
        render["flux_container"] = random.choice(ubuntu_views)
    else:
        render["flux_container"] = random.choice(rocky_views)
    return render


def generate_platform_version_minicluster(args, manifests, cfg, name):
    """
    Select platform AND version! No glibc errors here!
    """
    render = generate_basic_base(args, manifests, cfg, name)
    if "ubuntu" in render["image"] and "20.04" in render["image"]:
        render["flux_container"] = ubuntu_views[0]
    elif "ubuntu" in render["image"]:
        render["flux_container"] = ubuntu_views[1]
    elif "rocky" in render["image"] and "-8-" in render["image"]:
        render["flux_container"] = rocky_views[0]
    else:
        render["flux_container"] = rocky_views[1]
    return render


def generate_basic_base(args, manifests, cfg, name):
    """
    Base (shared) function for basic, platform-only, platform-version

    We are provided the container from the calling function, which has
    either considered (or not considered) os basic variables.
    """

    # Scope image selection to the matching platform
    images = manifests[args.platform]

    # Basic chooses just on the platform
    selected = random.choice(images)
    print(f'Selected image {selected["name"]}')

    # If gpu is in the name, we technically need to run the lmp_gpu command
    executable = "lmp"
    if "gpu" in selected["name"]:
        executable = "lmp_gpu"

    render = copy.deepcopy(cfg)
    render.update(
        {
            "image": selected["name"],
            "name": name,
            "executable": executable,
        }
    )
    return render


def generate_descriptive_minicluster(args, manifest_file, cfg, name):
    """
    Generate a descriptive minicluster

    For the descriptive case, we are going to run compspec (with a cache)
    to do image selection for us, accounting for a specific operating system,
    version (for glibc) and gpu (or most likely not to start - can be exposed later).
    """
    # This time, we aren't selected from images (manifests)
    # but rather starting with a base image (from reqs) and then using compspec
    flux_view = req[args.platform]
    selection = random.choice(flux_view)
    container = selection["image"]
    print(f"Selected flux view is {container}")

    # Use a common cache so we don't stress the registry
    cache_path = os.path.join(args.outdir, "cache")
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)

    # Generate metadata based on labels for compspec
    cmd = ["compspec", "match", "-i", manifest_file, "--cache", cache_path]

    # Now add the labels to match
    for key, value in selection["match"].items():
        cmd += ["--match", f"{key}={value}"]

    if args.gpu:
        cmd += ["--match", "org.supercontainers.hardware.gpu.available=yes"]
        executable = "lmp_gpu"
    else:
        cmd += ["--match", "org.supercontainers.hardware.gpu.available=no"]
        executable = "lmp"

    # Add in request for platform
    if args.platform == "amd64":
        cmd += ["--match", "io.archspec.cpu.target=amd64"]
    else:
        cmd += ["--match", "io.archspec.cpu.target=arm64"]

    # We only want ONE match, and random selection
    cmd += ["--single", "--randomize"]

    # Run command to get matches
    # Note we don't test for ZERO matches because we know we have them
    # Note this is currently slow and will speed up when we cache the graph
    print(" ".join(cmd))
    o, e = run_command(cmd, quiet=True)
    if "Found matches" not in o:
        print("Error with match, this should not happen, look at it.")
        import IPython

        IPython.embed()

    image = [x for x in o.split("\n") if x][-1]
    print(f"compspec has selected {image}")

    # For these, we assume the flux container is using ubuntu jammy
    # Note this can be changed
    render = copy.deepcopy(cfg)
    render.update(
        {
            "image": image,
            "name": name,
            "executable": executable,
            "flux_container": container,
        }
    )

    # If using intel-mpi, need to source this
    if "intel" in image:
        render["command"] = ". /opt/intel/mpi/latest/env/vars.sh"
    return render


def run(args, config_name, outdir):
    """
    Run the experiments for a given experiment type.
    """
    # Read in the template once
    experiment = configs[config_name]
    cfgs = experiment["config"]
    template = Template(read_file(experiment["template"]))

    # Keep record of all specs across iterations
    specs = {}

    # Load manifests.yaml
    manifests = load_yaml(args.manifests)

    # Organize manifests by gpu, os, and platform. We can do this since they are in the name (usually not)
    manifests = organize_manifests(manifests)

    # Make a directory for the logs
    log_dir = os.path.join(outdir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    for i in range(args.iters):

        # Run 1 of each experiment size for lammps
        # note that we can change how we do this (random, etc)
        for cfg in cfgs:

            # identifier for metadata
            size = cfg["size"]
            minicluster_name = f"lammps-{i}-size-{size}"

            # Generate the lammps job based on experiment mode

            # basic is platform only, and static - wild west! Most will fail
            if args.mode == "basic":
                render = generate_basic_minicluster(
                    args, manifests, cfg, minicluster_name
                )

            # Match ubuntu to ubuntu and rocky to rocky, that's it
            elif args.mode == "platform":
                render = generate_platform_minicluster(
                    args, manifests, cfg, minicluster_name
                )

            # Same but account for version too (get rid of glibc errors0
            elif args.mode == "platform-version":
                render = generate_platform_version_minicluster(
                    args, manifests, cfg, minicluster_name
                )

            # descriptive also accounts for gpu
            elif args.mode == "descriptive-basic":
                # We provide the manifests.yaml file instead - compspec does the selection from artifacts
                render = generate_descriptive_minicluster(
                    args, args.manifests, cfg, minicluster_name
                )

            size = cfg["size"]
            spec = {"params": render, "iter": i}
            name = spec["params"]["name"]

            # Generate and submit the template...
            minicluster_yaml = template.render(render)

            print(minicluster_yaml)
            # Save the minicluster yaml
            minicluster_yaml_file = os.path.join(
                log_dir, f"minicluster-{minicluster_name}.yaml"
            )
            write_file(minicluster_yaml, minicluster_yaml_file)

            # This submits the job, doesn't do more than that (e.g., waiting)
            start_time = datetime.utcnow()
            submit_job(minicluster_yaml)

            # Get logs and wait for completion (or error)
            get_logs(minicluster_name, spec, start_time, log_dir)
            end_time = datetime.utcnow()
            spec["total_wrapped_time"] = (end_time - start_time).seconds
            delete_minicluster(name)

    print(f"🧪️ Experiments are finished. See output in {outdir}")


def confirm_action(question):
    """
    Ask for confirmation of an action
    """
    response = input(question + " (yes/no)? ")
    while len(response) < 1 or response[0].lower().strip() not in "ynyesno":
        response = input("Please answer yes or no: ")
    if response[0].lower().strip() in "no":
        return False
    return True


def get_parser():
    parser = argparse.ArgumentParser(description="Run Descriptive Experiments")
    parser.add_argument(
        "--config-name",
        default="lammps-six",
        help="config name to use (defaults to lammps-six)",
    )
    parser.add_argument(
        "--iters",
        type=int,
        default=10,
        help="iterations to run (defaults to 10)",
    )
    parser.add_argument(
        "--manifests",
        help="path to manifests.yaml with image listing",
    )
    parser.add_argument(
        "--platform",
        default="amd64",
        choices=["amd64", "arm64"],
        help="node platform (amd64 or arm)",
    )
    parser.add_argument(
        "--mode",
        default="basic",
        choices=["basic", "platform", "platform-version", "descriptive-basic"],
        help="mode to run in (basic or descriptive)",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="specify wanting GPU for descriptive (only supported for this case)",
    )
    parser.add_argument(
        "--outdir",
        default=os.path.join(here, "results"),
        help="output directory for results",
    )
    return parser


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Ensure our template directory and templates exist
    if not os.path.exists(lammps_template):
        sys.exit(f"{lammps_template} does not exist.")

    outdir = os.path.abspath(args.outdir)

    # Also organize results by mode
    outdir = os.path.join(args.outdir, args.mode)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # We must have this file
    if not args.manifests or not os.path.exists(args.manifests):
        sys.exit("manifests.yaml must be defined and exist.")

    # Ensure the config is known
    if args.config_name not in configs:
        sys.exit(f"{args.config_name} is not a known configuration")

    compspec = None
    if args.mode.startswith("descriptive"):
        compspec = shutil.which("compspec")
        if not compspec:
            sys.exit(
                "compspec not found on the path, and is needed for descriptive experiments."
            )

    # Show parameters to the user
    print(f"▶️  Output directory: {outdir}")
    print(f"▶️       Config name: {args.config_name}")
    print(f"▶️        Iterations: {args.iters}")
    print(f"▶️              Mode: {args.mode}")

    # kubectl create -f cfg/service.yaml
    # kubectl create -f cfg/rbac.yaml

    if not confirm_action("Would you like to continue?"):
        sys.exit("Cancelled!")

    # Write the topology to this file
    topology_file = os.path.join(outdir, "topology.json")

    # Write cluster node configuration and return mapping
    node_topology = save_nodes(topology_file)

    try:
        run(args, args.config_name, outdir)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    main()
