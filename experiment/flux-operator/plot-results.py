#!/usr/bin/env python3

import argparse
import collections
import os
import re

import matplotlib.pyplot as plt
import metricsoperator.utils as utils
import pandas
import seaborn as sns

plt.style.use("bmh")
here = os.path.dirname(os.path.abspath(__file__))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Plot LAMMPS Descriptive Results",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--results",
        help="directory with raw results data",
        default=os.path.join(here, "results", "amd64"),
    )
    parser.add_argument(
        "--out",
        help="directory to save parsed results",
        default=os.path.join(here, "img"),
    )
    return parser


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
    indir = os.path.abspath(args.results)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Find input files (skip anything with test)
    files = find_inputs(indir)
    # specs = find_specs(indir)
    if not files:
        raise ValueError(f"There are no LAMMPS log files in {indir}")

    # This does the actual parsing of data into a formatted variant
    # Has keys results, iters, and columns
    df = parse_data(files)
    df.to_csv(os.path.join(outdir, "lammps-times.csv"))
    plot_results(df, outdir)


def plot_results(df, outdir):
    """
    Plot lammps results
    """
    # Rename:
    # basic should be platform (standard how a registry works)
    # platform is actually os
    # platform version is os version
    # descriptive basic can just be descriptive
    # control the order and subset
    df.experiment[df.experiment == "platform"] = "os"
    df.experiment[df.experiment == "platform-version"] = "os-version"
    df.experiment[df.experiment == "basic"] = "platform"
    df.experiment[df.experiment == "descriptive-basic"] = "descriptive"

    order = ["platform", "os", "os-version", "descriptive"]
    subset = df[df.experiment.isin(order)]

    colors = sns.color_palette("hls", 16)
    hexcolors = colors.as_hex()
    types = list(subset.reason.unique())
    types.sort()

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    make_plot(
        subset,
        title="LAMMPS Reasons for Failure Across Compatibility Dimensions",
        tag="lammps-reasons-failure",
        ydimension=None,
        xdimension="experiment",
        palette=palette,
        outdir=outdir,
        ext="png",
        plotname="lammps-reasons-failure",
        hue="reason",
        plot_type="hist",
        xlabel="Experiment",
        ylabel="Count",
        order=order,
    )

    # Show just descriptive basic variation
    subset = df[df.success == True]
    order = ["descriptive"]
    subset = df[df.experiment.isin(order)]

    colors = sns.color_palette("hls", 16)
    hexcolors = colors.as_hex()
    types = list(subset.reason.unique())
    types.sort()

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    make_plot(
        subset,
        title="LAMMPS Descriptive Wall Times",
        tag="lammps-decriptive-basic",
        ydimension="wall_time",
        xdimension="experiment",
        palette=palette,
        outdir=outdir,
        ext="png",
        plotname="lammps-descriptive-basic-wall-time",
        hue="reason",
        plot_type="bar",
        xlabel="Experiment",
        ylabel="Wall time (seconds)",
        order=order,
    )

    # Filter down to successful runs
    subset = df[df.success == True]
    order = ["descriptive", "mpich", "intel-mpi", "openmpi"]
    subset = df[df.experiment.isin(order)]

    colors = sns.color_palette("hls", 16)
    hexcolors = colors.as_hex()
    types = list(subset.reason.unique())
    types.sort()

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    make_plot(
        subset,
        title="LAMMPS Successful Runs (Wall Times)",
        tag="lammps-success-runs",
        ydimension="wall_time",
        xdimension="experiment",
        palette=palette,
        outdir=outdir,
        ext="png",
        plotname="lammps-success-runs",
        hue="reason",
        plot_type="bar",
        xlabel="Experiment",
        ylabel="Wall time (seconds)",
        order=order,
    )


def get_reason_for_failure(log):
    """
    Get reason for failure
    """
    if "Total wall time" in log:
        return "success"
    if "libcuda.so.1: cannot open shared object file" in log:
        return "missing gpu"
    if "Other MPI error" in log:
        return "mpi error"
    # note this can be GLIBC or GLIBCXX
    if "GLIBC" in log and "not found" in log:
        return "os abi issue"
    else:
        print("FOUND NEW ISSUE")
        import IPython

        IPython.embed()


def parse_data(files):
    """
    Given a listing of files, parse into results data frame
    """
    # We used the same size / ranks for all of these
    # And it doesn't really matter
    # Parse into data frame
    df = pandas.DataFrame(
        columns=[
            "success",
            "reason",  # reason for failure (or success)
            "experiment",
            "wall_time",
        ]
    )
    idx = 0

    for filename in files:
        # Skip events files
        if "topology" in filename:
            continue
        parsed = os.path.relpath(filename, here)
        experiment = parsed.split(os.sep)[2]

        # This can be split into pieces by ===
        item = utils.read_file(filename)
        reason = get_reason_for_failure(item)

        # Find the time if we were successful
        wall_time = None
        if reason == "success":
            log = [x for x in item.split("\n") if "Total wall time" in x]

            # This is the LAMMPS section with wall time
            line = [x for x in log[0].split("\n") if "Total wall time" in x][0]
            rawtime = line.split(":", 1)[-1].strip()
            wall_time = utils.timestr2seconds(rawtime)

        # We just care about times for the data frame
        df.loc[idx, :] = [
            reason == "success",
            reason,
            experiment,
            wall_time,
        ]
        idx += 1
    return df


def make_plot(
    df,
    title,
    tag,
    ydimension,
    xdimension,
    palette,
    xlabel,
    ylabel,
    ext="pdf",
    plotname="lammps",
    plot_type="violin",
    hue="experiment",
    outdir="img",
    order=None,
):
    """
    Helper function to make common plots.
    """
    plotfunc = sns.boxplot
    if plot_type == "hist":
        plotfunc = sns.countplot
    if plot_type == "violin":
        plotfunc = sns.violinplot

    ext = ext.strip(".")
    plt.figure(figsize=(20, 12))
    sns.set_style("dark")
    if plot_type != "hist":
        ax = plotfunc(
            x=xdimension, y=ydimension, hue=hue, data=df, whis=[5, 95], palette=palette
        )
    else:
        ax = plotfunc(
            x=xdimension, y=ydimension, hue=hue, data=df, palette=palette, order=order
        )
    plt.title(title)
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    plt.savefig(os.path.join(outdir, f"{tag}_{plotname}.{ext}"))
    plt.clf()


if __name__ == "__main__":
    main()
