#!/usr/bin/env python3

import argparse
import json
import os
import random
import fnmatch

here = os.path.dirname(os.path.abspath(__file__))

# Descriptive modes of metadata
modes = [
    "basic",
    "platform-version",
    "descriptive-basic",
]

# The truth of where the binary should actually run (where it was built)
truth = {
    "lammps-20230802.2-l75zzkprajipt5e5daomwfyxe3meus3q.json": "corona",
    "lammps-20230802.2-nof5qz5k6lrafqdd6bnzpu3va5hj6qbu.json": "lassen",
    "lammps-20230802.2-thmw3hvmel7xuew7cipxtspzrsu7nxq3.json": "lassen",
    "lammps-20230802.2-fuuonv3y4cddfswssbuse5jfp2cjmn7p.json": "quartz",
    "lammps-20230802.2-rqspxlxcrxzhov5rlojh2rrus3x6mvbh.json": "quartz",
}


def recursive_find(base, pattern="spec.json"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def write_json(content, filename):
    """
    Write json to file
    """
    with open(filename, "w") as fd:
        fd.write(json.dumps(content, indent=4))


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


def read_json(filename):
    """
    Read json from file
    """
    return json.loads(read_file(filename))


def run(args, outdir):
    """
    Run the experiments across modes.
    """
    # Read in metadata for each
    specs = {}

    # Keep track of systems
    systems = set()
    hosts = {}

    for filename in recursive_find(args.specs_dir, "*.json"):
        systems.add(os.path.basename(os.path.dirname(filename)))
        specs[os.path.basename(filename)] = read_json(filename)
    systems = list(systems)

    # Create lookup of hosts
    for filename in recursive_find(args.hosts_dir, "*.json"):
        hostname = (
            os.path.basename(filename).replace(".json", "").replace("compspec-", "")
        )
        hosts[hostname] = read_json(filename)

    # Create dumb lookups to select from each. E.g,. we will take overlapping sets
    # to decide on a host. GPU we are setting here, we only built CUDA for lassen
    select = {
        "platform": {},
        "gpu": {"yes": ["lassen"], "no": ["corona", "quartz"]},
        "os": {},
        # Note that I have to manually add openmpi here, because it wasn't on the system
        # It was provided by spack. This is why the system extractor won't be sufficient
        # for software that is coming from an environment.
        "mpi": {
            "version": {},
            "variant": {"openmpi": ["corona"], "mvapich2": ["quartz"]},
        },
    }
    for hostname, host in hosts.items():
        # platform
        platform = host["results"]["system"]["sections"]["arch"]["name"]
        if platform not in select["platform"]:
            select["platform"][platform] = []
        select["platform"][platform].append(hostname)

        # Host os name (we don't need version here, no mixing of views)
        os_name = host["results"]["nfd"]["sections"]["system"]["osrelease.ID"]
        if os_name not in select["os"]:
            select["os"][os_name] = []
        select["os"][os_name].append(hostname)

        os_version = host["results"]["nfd"]["sections"]["system"][
            "osrelease.VERSION_ID"
        ]
        if os_version not in select["os"]:
            select["os"][os_version] = []
        select["os"][os_version].append(hostname)

        # We need mpi available NOTE: bug here that some have sections, some not
        if "sections" in host["results"]["library"]:
            mpi_variant = host["results"]["library"]["sections"]["mpi"]["variant"]
            mpi_version = host["results"]["library"]["sections"]["mpi"]["version"]
        else:
            mpi_variant = host["results"]["library"]["mpi"]["variant"]
            mpi_version = host["results"]["library"]["mpi"]["version"]

        # MPI variant and version
        if mpi_variant not in select["mpi"]["variant"]:
            select["mpi"]["variant"][mpi_variant] = []
        select["mpi"]["variant"][mpi_variant].append(hostname)

        if mpi_version not in select["mpi"]["version"]:
            select["mpi"]["version"][mpi_version] = []
        select["mpi"]["version"][mpi_version].append(hostname)

    # Keep a matrix of results, basically store 1 if we got it right, 0 for wrong
    results = {mode: {} for mode in modes}

    for mode in modes:
        for specname, spec in specs.items():
            # Name of the binary to store results
            binary = specname.replace(".json", "")

            # The truth about where it needs to run
            needed = truth[specname]

            if binary not in results[mode]:
                results[mode][binary] = []

            # Pull out what the spec needs, we might not use all of it for each mode
            needed_platform = spec["compatibilities"][1]["attributes"]["cpu.target"]
            needed_variant = spec["compatibilities"][0]["attributes"][
                "mpi.implementation"
            ]

            # This might not be meaningful unless there are OS ABI issues
            needed_os_version = spec["compatibilities"][0]["attributes"]["os.release"]

            # What we have to choose from
            systems_for_platform = select["platform"][needed_platform]
            os_versions = select["os"][needed_os_version]
            mpi_variants = select["mpi"]["variant"][needed_variant]

            for iter in range(args.iters):
                # Basic mode, just select based on platform
                if mode == "basic":
                    choice = random.choice(select["platform"][needed_platform])
                    results[mode][binary].append(
                        {
                            "selected": choice,
                            "needed": needed,
                            "correct": choice == needed,
                        }
                    )

                # This adds in os name, which isn't meaningful because they all are rhel. We are going to
                # skip this case and just consider version
                elif mode == "platform-version":
                    choice = None
                    choices = list(
                        set(systems_for_platform).intersection(set(os_versions))
                    )
                    if choices:
                        choice = random.choice(choices)
                    results[mode][binary].append(
                        {
                            "selected": choice,
                            "needed": needed,
                            "correct": choice == needed,
                        }
                    )

                # This is all including MPI, but I don't think we need that because we don't have many choices
                elif mode == "descriptive-basic":
                    choice = None
                    choices = list(
                        set(systems_for_platform)
                        .intersection(set(os_versions))
                        .intersection(mpi_variants)
                    )
                    if choices:
                        choice = random.choice(choices)
                    results[mode][binary].append(
                        {
                            "selected": choice,
                            "needed": needed,
                            "correct": choice == needed,
                        }
                    )

    print(f"🧪️ Experiments are finished. See output in {outdir}")
    write_json(results, os.path.join(outdir, "simulation-results.json"))


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
    parser = argparse.ArgumentParser(
        description="Simulate Descriptive Spack Experiments"
    )
    parser.add_argument(
        "--specs-dir",
        dest="specs_dir",
        help="directory with specs to make assessment for",
    )
    parser.add_argument(
        "--hosts-dir",
        dest="hosts_dir",
        help="directory with host information",
    )
    parser.add_argument(
        "--outdir",
        default=os.path.join(here, "results"),
        help="output directory for results",
    )
    parser.add_argument(
        "--iters",
        default=20,
        help="number of iterations to run for simulation",
        type=int,
    )
    return parser


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()
    outdir = os.path.abspath(args.outdir)

    # We will write data files here
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Show parameters to the user
    print(f"▶️  Output directory: {outdir}")
    print(f"▶️       Config name: {args.specs_dir}")
    print(f"▶️        Iterations: {args.hosts_dir}")

    try:
        run(args, outdir)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    main()
