raise Exception("This code uses old loader, please refactor.")
import json
import numpy as np
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import collections

df = MergedAnnotations().df

statistics_collector = {
    schema: collections.defaultdict(list)
    for schema in ["esa", "gesa", "gemba", "mqm", "wmt"]
}


for _, row in df.iterrows():
    if type(row["gemba_mqm_span_errors_gemba"]) != list:
        continue
    span_errors_gemba = row["gemba_mqm_span_errors_gemba"]
    span_errors_gesa = json.loads(row["span_errors_gemba"])
    span_errors_esa = json.loads(row["span_errors_esa"])
    span_errors_mqm = json.loads(row["span_errors_mqm"])
    span_errors_wmt = row["wmt_mqm_span_errors"]
    if span_errors_wmt == "None" or span_errors_wmt is None:
        span_errors_wmt = []

    statistics_collector["gemba"]["segment_count"].append(len(span_errors_gemba))
    statistics_collector["gesa"]["segment_count"].append(len(span_errors_gesa))
    statistics_collector["esa"]["segment_count"].append(len(span_errors_esa))
    statistics_collector["mqm"]["segment_count"].append(len(span_errors_mqm))
    statistics_collector["wmt"]["segment_count"].append(len(span_errors_wmt))

    statistics_collector["gemba"]["segment_count_minor"].append(len([x for x in span_errors_gemba if x["severity"] == "minor"]))
    statistics_collector["gesa"]["segment_count_minor"].append(len([x for x in span_errors_gesa if x["severity"] == "minor"]))
    statistics_collector["esa"]["segment_count_minor"].append(len([x for x in span_errors_esa if x["severity"] == "minor"]))
    statistics_collector["mqm"]["segment_count_minor"].append(len([x for x in span_errors_mqm if x["severity"] == "minor"]))
    statistics_collector["wmt"]["segment_count_minor"].append(len([x for x in span_errors_wmt if x["severity"] == "minor"]))

    statistics_collector["gemba"]["segment_count_major"].append(len([x for x in span_errors_gemba if x["severity"] == "major"]))
    statistics_collector["gesa"]["segment_count_major"].append(len([x for x in span_errors_gesa if x["severity"] == "major"]))
    statistics_collector["esa"]["segment_count_major"].append(len([x for x in span_errors_esa if x["severity"] == "major"]))
    statistics_collector["mqm"]["segment_count_major"].append(len([x for x in span_errors_mqm if x["severity"] in {"major", "critical"}]))
    statistics_collector["wmt"]["segment_count_major"].append(len([x for x in span_errors_wmt if x["severity"] in {"major", "critical"}]))

    statistics_collector["gesa"]["score"].append(row["score_gemba"])
    statistics_collector["esa"]["score"].append(row["score_esa"])

for schema, schema_v in statistics_collector.items():
    print(schema, {k: f"{np.average(v):.2f}" for k, v in schema_v.items()})

print("Now percentile of total segment count")
total_segments = {
    schema: np.sum(statistics_collector[schema]["segment_count"])
    for schema in statistics_collector.keys()
}
for schema, schema_v in statistics_collector.items():
    print(schema, {k: f"{np.sum(v)/total_segments[schema]:.1%}" for k, v in schema_v.items()})

# plotting part
import matplotlib.pyplot as plt
import ESA.figutils as figutils

figutils.matplotlib_default()

fig = plt.figure(figsize=(4, 1.8))

KWARGS = {
    "alpha": 0.7,
    "width": 0.3,
}
BINS_BASE = np.linspace(0, 5, 6)

OFFSET_X = 0.3

ROW_COUNT = len(statistics_collector["esa"]["segment_count"])
plt.hist(
    np.array(statistics_collector["esa"]["segment_count"])-OFFSET_X,
    label="ESA",
    bins=BINS_BASE-OFFSET_X,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)
plt.hist(
    np.array(statistics_collector["gesa"]["segment_count"]),
    label="ESA$^\mathrm{AI}$",
    bins=BINS_BASE,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)
plt.hist(
    np.array(statistics_collector["gemba"]["segment_count"])+OFFSET_X,
    label="GEMBA",
    bins=BINS_BASE+OFFSET_X,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)

plt.gca().spines[['top', 'right']].set_visible(False)
plt.legend()
plt.xlim(None, 4.5)
plt.xticks([0, 1, 2, 3, 4])
plt.yticks([0, 0.2, 0.6, 0.8], ["0%", "20%", "60%", "80%"])

plt.xlabel("Error span count", labelpad=-2)
plt.ylabel("Freq.", labelpad=-10)
plt.tight_layout(pad=0)
plt.savefig("figures/overview_segment_count.pdf")
plt.show()