#!/usr/bin/env python3

import matplotlib.pyplot as plt
import pandas
import seaborn as sns
import scipy.spatial as sp, scipy.cluster.hierarchy as hc
from sklearn.metrics.pairwise import pairwise_distances

plt.style.use("bmh")


def main():
    columns = [
        "io.archspec.cpu.target",
        "org.supercontainers.os.vendor",
        "org.supercontainers.os.version",
        "org.supercontainers.hardware.gpu.available",
        "mpi.implementation",
    ]
    df = pandas.DataFrame(columns=columns)

    # Add each row manually
    rows = ["platform", "os", "os-version", "descriptive"]
    df.loc["platform", :] = [1, 0, 0, 0, 0]
    df.loc["os", :] = [1, 1, 0, 0, 0]
    df.loc["os-version", :] = [1, 1, 1, 0, 0]
    df.loc["descriptive", :] = [1, 1, 1, 1, 0]

    dist = pandas.DataFrame(pairwise_distances(df, metric="cosine"))
    # Needs rto be absolute 0
    for i in range(dist.shape[0]):
        dist.loc[i, i] = 0

    linkage = hc.linkage(sp.distance.squareform(dist), method="average")
    dist.columns = rows
    dist.index = rows
    fig = sns.clustermap(dist, row_linkage=linkage, col_linkage=linkage, cmap="mako")
    # plt.title("Compatibility Gradient (Cosine Distance)")
    plt.setp(fig.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
    fig.savefig("compatibility-matrix.png")


if __name__ == "__main__":
    main()
