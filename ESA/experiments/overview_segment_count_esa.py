import ESA.figutils as figutils
import matplotlib.pyplot as plt
import collections
import numpy as np
from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(
    ["ESA-1", "ESA-2", "MQM-1"], only_overlap=False).dropna()
figutils.matplotlib_default()


statistics_collector = {
    schema: collections.defaultdict(list)
    for schema in ["esa", "mqm"]
}

for _, row in df.iterrows():
    statistics_collector["esa"]["segment_count"].append(
        len(row["ESA-1_error_spans"]))
    statistics_collector["mqm"]["segment_count"].append(
        len(row["MQM-1_error_spans"]))

    statistics_collector["esa"]["segment_count_minor"].append(
        len([x for x in row["ESA-1_error_spans"] if x["severity"] == "minor"]))
    statistics_collector["mqm"]["segment_count_minor"].append(
        len([x for x in row["MQM-1_error_spans"] if x["severity"] == "minor"]))

    statistics_collector["esa"]["segment_count_major"].append(
        len([x for x in row["ESA-1_error_spans"] if x["severity"] == "major"]))
    statistics_collector["mqm"]["segment_count_major"].append(len(
        [x for x in row["MQM-1_error_spans"] if x["severity"] in {"major", "critical"}]))

    statistics_collector["esa"]["score"].append(row["ESA-1_score"])
    statistics_collector["esa"]["score_mqm"].append(row["ESA-1_score_mqm"])
    statistics_collector["mqm"]["score"].append(row["MQM-1_score"])

for schema, schema_v in statistics_collector.items():
    print(schema, {k: f"{np.average(v):.2f}" for k, v in schema_v.items()})

print("Now percentile of total segment count")
total_segments = {
    schema: np.sum(statistics_collector[schema]["segment_count"])
    for schema in statistics_collector.keys()
}
for schema, schema_v in statistics_collector.items():
    print(schema, {
          k: f"{np.sum(v)/total_segments[schema]:.1%}" for k, v in schema_v.items()})

# first plot
fig = plt.figure(figsize=(4, 1.5))

BINS_BASE = np.linspace(1, 6, 6)
OFFSET_X = 0.3
ROW_COUNT = len(statistics_collector["esa"]["segment_count_minor"])

bins_y, _, _ = plt.hist(
    np.array(statistics_collector["esa"]["segment_count_major"])-OFFSET_X,
    label="ESA Major",
    bins=BINS_BASE-OFFSET_X,
    color=figutils.COLORS[0],
    alpha=0.8,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    width=0.3,
)
plt.hist(
    np.array(statistics_collector["esa"]["segment_count_minor"])-OFFSET_X,
    label="ESA Minor",
    color=figutils.COLORS[0],
    alpha=0.3,
    bottom=bins_y,
    bins=BINS_BASE-OFFSET_X,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    width=0.3,
)
bins_y, _, _ = plt.hist(
    np.array(statistics_collector["mqm"]["segment_count_major"]),
    label="MQM Major",
    color=figutils.COLORS[1],
    alpha=0.8,
    bins=BINS_BASE,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    width=0.3,
)
plt.hist(
    np.array(statistics_collector["mqm"]["segment_count_minor"]),
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
    s=f"avg ESA error spans {np.average(statistics_collector['esa']['segment_count']):.2f}\n" +
    f"avg MQM error spans {np.average(statistics_collector['mqm']['segment_count']):.2f}",
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
fig, ax = plt.subplots(3, 1, figsize=(4, 2.2))


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
    statistics_collector["esa"]["score"],
    color=figutils.COLORS[0],
    bins=20,
)
ax[0].set_ylabel("ESA", rotation=0)
ax[0].yaxis.set_label_coords(0.096, 0.3)

ax[1].hist(
    statistics_collector["esa"]["score_mqm"],
    color=figutils.COLORS[0], alpha=0.4,
    bins=20,
)
ax[1].set_ylabel(r"ESA$_\mathrm{MQM}$", rotation=0)
ax[1].yaxis.set_label_coords(0.13, 0.3)

ax[2].hist(
    statistics_collector["mqm"]["score"],
    color=figutils.COLORS[1],
    bins=20,
)
ax[2].set_ylabel("MQM", rotation=0)
ax[2].yaxis.set_label_coords(0.1, 0.3)


ax[2].set_xlabel("Score")
for ax_i, ax in enumerate(ax):
    ax.set_yticks([])
    if ax_i != 0:
        ax.set_xlim(-25, 0)
    else:
        ax.set_xlim(0, 100)
    # ax.set_ylim(1, None)
    ax.spines[['top', 'right', 'left']].set_visible(False)


plt.tight_layout(pad=0)
plt.savefig("PAPER_ESA/generated_plots/score_distribution.pdf")
plt.show()
