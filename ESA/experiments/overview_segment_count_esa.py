import ESA.figutils as figutils
import matplotlib.pyplot as plt
import collections
import numpy as np
import ipdb
import pandas as pd
from ESA.annotation_loader import AnnotationLoader
from ESA.utils import PROTOCOL_DEFINITIONS


def overview_segment_count_esa(annotations_loader):
    df = annotations_loader.get_view(
        ["ESA-1", "ESA-2", "MQM-1", "WMT-MQM"], only_overlap=False).dropna()
    figutils.matplotlib_default()

    schemas = ["ESA-1", "ESA-2", "MQM-1", "WMT-MQM"]
    statistics_collector = {
        schema: collections.defaultdict(list)
        for schema in schemas
    }

    for _, row in df.iterrows():
        for schema in schemas:
            statistics_collector[schema]["segment_count"].append(len(row[f"{schema}_error_spans"]))
            statistics_collector[schema]["segment_count_minor"].append(
                len([x for x in row[f"{schema}_error_spans"] if x["severity"] == "minor"]))
            statistics_collector[schema]["segment_count_major"].append(
                len([x for x in row[f"{schema}_error_spans"] if x["severity"] in {"major", "critical"}]))
            if "MQM" not in schema:
                statistics_collector[schema]["score"].append(row[f"{schema}_score"])
                statistics_collector[schema]["score_mqm"].append(row[f"{schema}_score_mqm"])
            else:
                statistics_collector[schema]["score"].append(0)
                statistics_collector[schema]["score_mqm"].append(row[f"{schema}_score"])

    table = {}
    for schema, schema_v in statistics_collector.items():
        schema = PROTOCOL_DEFINITIONS[schema]["name"]
        table[schema] = {}
        table[schema]["\# error spans"] = f'{np.average(schema_v["segment_count"]):.2f}'
        major = np.sum(schema_v["segment_count_major"])
        minor = np.sum(schema_v["segment_count_minor"])
        table[schema]["\% minor"] = f'{100*minor/(major+minor):.0f}\%'
        table[schema]["\% major"] = f'{100*major/(major+minor):.0f}\%'
        score = np.average(schema_v["score"])
        if score == 0:
            score = ""
        else:
            score = f"{score:.1f}"
        score_mqm = np.average(schema_v["score_mqm"])
        table[schema]["Score (MQM-like)"] = f"{score} ({score_mqm:.1f})"

    df = pd.DataFrame(table)
    # save to latex PAPER_ESA/generated_plots/overview_segment_count_esa.tex
    df.to_latex("PAPER_ESA/generated_plots/overview_segment_count_esa.tex", escape=False)

    # first plot
    fig = plt.figure(figsize=(4, 1.5))

    BINS_BASE = np.linspace(1, 6, 6)
    OFFSET_X = 0.3
    ROW_COUNT = len(statistics_collector["ESA-1"]["segment_count_minor"])

    bins_y, _, _ = plt.hist(
        np.array(statistics_collector["ESA-1"]["segment_count_major"])-OFFSET_X,
        label="ESA Major",
        bins=BINS_BASE-OFFSET_X,
        color=figutils.COLORS[0],
        alpha=0.8,
        weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
        width=0.3,
    )
    plt.hist(
        np.array(statistics_collector["ESA-1"]["segment_count_minor"])-OFFSET_X,
        label="ESA Minor",
        color=figutils.COLORS[0],
        alpha=0.3,
        bottom=bins_y,
        bins=BINS_BASE-OFFSET_X,
        weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
        width=0.3,
    )
    bins_y, _, _ = plt.hist(
        np.array(statistics_collector["MQM-1"]["segment_count_major"]),
        label="MQM Major",
        color=figutils.COLORS[1],
        alpha=0.8,
        bins=BINS_BASE,
        weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
        width=0.3,
    )
    plt.hist(
        np.array(statistics_collector["MQM-1"]["segment_count_minor"]),
        label="MQM Minor",
        color=figutils.COLORS[1],
        alpha=0.3,
        bottom=bins_y,
        bins=BINS_BASE,
        weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
        width=0.3,
    )

    plt.text(
        0.5, 0.5,
        s=f"avg ESA error spans {np.average(statistics_collector['ESA-1']['segment_count']):.2f}\n" +
        f"avg MQM error spans {np.average(statistics_collector['MQM-1']['segment_count']):.2f}",
        transform=plt.gca().transAxes,
        fontsize=9,
        fontweight="bold"
    )

    plt.gca().spines[['top', 'right']].set_visible(False)
    plt.legend(ncol=2)
    plt.xlim(None, 4.5)
    plt.yticks([0, 0.2], ["0%", "20%"])

    plt.xlabel("Error span count", labelpad=-2)
    plt.ylabel("Frequency" + " "*5, labelpad=-10)
    plt.tight_layout(pad=0)
    plt.savefig("PAPER_ESA/generated_plots/overview_segment_count_esa.pdf")
    plt.show()

    # second plot
    fig, ax = plt.subplots(4, 1, figsize=(4, 3))

    def half_violin(v1, color, alpha=0.7):
        for pc in v1['bodies']:
            pc.set_facecolor(color)
            pc.set_alpha(alpha)
            pc.set_aa(True)
            # get the center
            m = np.mean(pc.get_paths()[0].vertices[:, 1])
            # modify the paths to not go further left than the center
            pc.get_paths()[0].vertices[:, 1] = np.clip(
                pc.get_paths()[0].vertices[:, 1],
                m, np.inf
            )

    ax[0].hist(
        statistics_collector["ESA-1"]["score"],
        color=figutils.COLORS[0],
        bins=40,
    )
    ax[0].set_ylabel("ESA", rotation=0)
    ax[0].yaxis.set_label_coords(0.096, 0.3)

    ax[1].hist(
        [x for x in statistics_collector["ESA-1"]["score_mqm"] if x >= -15],
        color=figutils.COLORS[0], alpha=0.4,
        bins=40,
    )
    ax[1].set_ylabel(r"ESA$_\mathrm{MQM}$", rotation=0)
    ax[1].yaxis.set_label_coords(0.13, 0.3)

    ax[2].hist(
        [x for x in statistics_collector["MQM-1"]["score_mqm"] if x >= -15],
        color=figutils.COLORS[1],
        bins=40,
    )
    ax[2].set_ylabel("MQM", rotation=0)
    ax[2].yaxis.set_label_coords(0.1, 0.3)

    ax[3].hist(
        [x for x in statistics_collector["WMT-MQM"]["score_mqm"] if x >= -15],
        color=figutils.COLORS[1], alpha=0.4,
        bins=40,
    )
    ax[3].set_ylabel("MQM$^\mathrm{WMT}$", rotation=0)
    ax[3].yaxis.set_label_coords(0.14, 0.3)

    ax[3].set_xlabel("Score")
    for ax_i, ax in enumerate(ax):
        ax.set_yticks([])
        if ax_i == 0:
            ax.set_xlim(0, 100)
        else:
            ax.set_xlim(-15, 0)
        ax.spines[['top', 'right', 'left']].set_visible(False)

    plt.tight_layout(pad=0)
    plt.subplots_adjust(hspace=0.5)
    plt.savefig("PAPER_ESA/generated_plots/score_distribution.pdf")
    plt.show()


if __name__ == '__main__':
    overview_segment_count_esa(AnnotationLoader(refresh_cache=False))
