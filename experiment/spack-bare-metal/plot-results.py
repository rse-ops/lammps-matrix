#!/usr/bin/env python3

import argparse
import collections
import os
import re
import json

import matplotlib.pyplot as plt
import pandas
import seaborn as sns

plt.style.use("bmh")
here = os.path.dirname(os.path.abspath(__file__))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Plot Spack Simulation Results",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--results",
        help="results file",
        default=os.path.join(here, "results", "simulation-results.json"),
    )
    parser.add_argument(
        "--out",
        help="directory to save parsed results",
        default=os.path.join(here, "img"),
    )
    return parser


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


def recursive_find(base, pattern="specs.json"):
    """
    Recursively find and yield files matching a glob pattern.
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


def find_inputs(input_dir):
    """
    Find inputs (results files)
    """
    files = []
    for filename in recursive_find(input_dir, pattern="log"):
        # We only have data for small
        files.append(filename)
    return files


def find_specs(input_dir):
    """
    Find specs files
    """
    files = []
    for filename in recursive_find(input_dir, pattern="specs.json"):
        # We only have data for small
        files.append(filename)
    return files


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Output images and data
    outdir = os.path.abspath(args.out)
    infile = os.path.abspath(args.results)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    df, levels = parse_data(infile)
    print(levels)
    df.to_csv(os.path.join(outdir, "simulation-results.csv"))


def parse_data(infile):
    """
    Given a listing of files, parse into results data frame

    We care about correct vs incorrect for each
    """
    raw = read_json(infile)

    df = pandas.DataFrame(
        columns=[
            "needed",
            "choice",
            "correct",
            "binary",
            "experiment",
        ]
    )
    idx = 0

    for experiment, results in raw.items():
        for binary, iters in results.items():
            for result in iters:
                # We just care about times for the data frame
                df.loc[idx, :] = [
                    result["needed"],
                    result["selected"],
                    result["correct"],
                    binary,
                    experiment,
                ]
                idx += 1

    # Keep track of counts of correct / incorrect
    levels = {}
    for experiment in df.experiment.unique():
        subset = df[df.experiment == experiment]
        total = subset.shape[0]
        correct = subset[subset.correct == True].shape[0]
        levels[experiment] = correct / total

    return df, levels


if __name__ == "__main__":
    main()
