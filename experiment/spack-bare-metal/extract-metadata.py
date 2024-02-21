#!/usr/bin/env python3

import argparse
import copy
import json
import os
import subprocess
import shutil
import fnmatch
import random
import sys
import tempfile
import yaml
import json
from datetime import datetime

from jinja2 import Template

here = os.path.dirname(os.path.abspath(__file__))
compspec_json = os.path.join(here, "compspec-system.json")
if not os.path.exists(compspec_json):
    sys.exit(
        "Please extract a compspec-system.json first: comspec extract --name system --out compspec-system.json"
    )


def write_json(content, filename):
    """
    Write json to file
    """
    with open(filename, "w") as fd:
        fd.write(json.dumps(content, indent=4))


def recursive_find(base, pattern="spec.json"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


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
    return json.loads(read_file(filename))


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


# Template to populate for each package
template = {
    "version": "0.0.0",
    "kind": "CompatibilitySpec",
    "metadata": {
        "name": "lammps-prototype",
        "schemas": {
            "io.archspec": "https://raw.githubusercontent.com/supercontainers/compspec/main/archspec/compspec.json",
            "org.supercontainers": "https://raw.githubusercontent.com/supercontainers/compspec/main/supercontainers/compspec.json",
        },
    },
    "compatibilities": [
        {
            "name": "org.supercontainers",
            "version": "0.0.0",
            "attributes": {
                "hardware.gpu.available": None,  # "no",
                "mpi.implementation": None,  # "intel-mpi",
                "mpi.version": None,  # "2021.8",
                "os.name": None,  # "Rocky Linux 9.3 (Blue Onyx)",
                "os.release": None,  # "9.3",
                "os.vendor": None,  # "rocky",
                "os.version": None,  # "9.3"
            },
        },
        {
            "name": "io.archspec",
            "version": "0.0.0",
            "attributes": {
                "cpu.model": None,  # "13th Gen Intel(R) Core(TM) i5-1335U",
                "cpu.target": None,  # "amd64",
                "cpu.vendor": None,  # "GenuineIntel"
            },
        },
    ],
}


def run(args, outdir):
    """
    Run the experiments for a given experiment type.
    """
    opt_dir = os.path.join(args.spack_root, "opt")
    packages = []
    for spec_file in recursive_find(opt_dir, "spec.json"):
        if args.package not in spec_file:
            continue
        packages.append(os.path.dirname(os.path.dirname(spec_file)))
    print(f"Found {len(packages)} package for {args.package}")

    # Load host compspec metadata
    compspec = read_json(compspec_json)

    # For each, read in the spec.json and
    for package in packages:
        spec = copy.deepcopy(template)
        spec_json = os.path.join(package, ".spack", "spec.json")
        env_file = os.path.join(package, ".spack", "install_environment.json")
        spack_spec = read_json(spec_json)
        environ = read_json(env_file)

        # This isn't exactly right, but it matches what we did for kubernetes experiments
        spec["compatibilities"][0]["attributes"]["os.name"] = environ["host_os"]
        spec["compatibilities"][1]["attributes"]["cpu.target"] = compspec["extractors"][
            "system"
        ]["sections"]["arch"]["name"]
        spec["compatibilities"][1]["attributes"]["cpu.model"] = environ["host_target"]

        spec["compatibilities"][1]["attributes"]["cpu.vendor"] = compspec["extractors"][
            "system"
        ]["sections"]["processor"]["0.vendor"]
        spec["compatibilities"][1]["attributes"]["cpu.vendor"] = compspec["extractors"][
            "system"
        ]["sections"]["processor"]["0.target"]

        # hardware.gpu.available

        spec["compatibilities"][0]["attributes"]["os.release"] = compspec["extractors"][
            "system"
        ]["sections"]["os"]["release"]
        spec["compatibilities"][0]["attributes"]["os.vendor"] = compspec["extractors"][
            "system"
        ]["sections"]["os"]["vendor"]

        # Get the specific MPI
        mpi = [
            x
            for x in spack_spec["spec"]["nodes"][0]["dependencies"]
            if "mpi" in x["name"]
        ]
        mpi = [x for x in spack_spec["spec"]["nodes"] if x["hash"] == mpi[0]["hash"]]
        spec["compatibilities"][0]["attributes"]["mpi.implementation"] = mpi[0]["name"]
        spec["compatibilities"][0]["attributes"]["mpi.version"] = mpi[0]["version"]

        # For now, don't add GPU
        has_gpu = "no"
        test = [x["name"] for x in spack_spec["spec"]["nodes"] if "cuda" in x["name"]]
        if test:
            has_gpu = "yes"
        spec["compatibilities"][0]["attributes"]["hardware.gpu.available"] = has_gpu

        # Write to output file
        package_hash = "%s.json" % os.path.join(args.outdir, os.path.basename(package))
        write_json(spec, package_hash)


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
    parser = argparse.ArgumentParser(description="Extract Spack Metadata")
    parser.add_argument(
        "--spack-root",
        dest="spack_root",
        default=os.getcwd(),
        help="spack root",
    )
    parser.add_argument(
        "--package",
        help="package name to seach for",
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
    if not os.path.exists(args.spack_root):
        sys.exit(f"{args.spack_root} does not exist.")

    if not args.package:
        sys.exit("Please provide the name of a package with --package")
    outdir = os.path.abspath(args.outdir)
    try:
        run(args, outdir)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    main()
