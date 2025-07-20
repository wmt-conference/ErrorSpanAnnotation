import numpy as np
from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view()
import collections

statistics_collector = {
    schema: collections.defaultdict(list)
    for schema in ["gemba", "esa", "esaai", "mqm", "wmt"]
}

def get_spans(spans):
    return {(x["start_i"], x["end_i"]) for x in spans}

def get_spans_wmt(spans):
    return {(x["start"], x["end"]) for x in spans}

for _, row in df.iterrows():
    spans_gemba = row["LLM_error_spans"]
    spans_esaai = row["ESAAI-1_error_spans"]
    spans_esa = row["ESA-1_error_spans"]
    spans_mqm = row["MQM-1_error_spans"]
    spans_wmt = row["WMT-MQM_error_spans"]

    statistics_collector["gemba"]["segment_count"].append(len(spans_gemba))
    statistics_collector["esaai"]["segment_count"].append(len(spans_esaai))
    statistics_collector["esa"]["segment_count"].append(len(spans_esa))
    statistics_collector["mqm"]["segment_count"].append(len(spans_mqm))
    statistics_collector["wmt"]["segment_count"].append(len(spans_wmt))

    statistics_collector["gemba"]["segment_count_minor"].append(len([x for x in spans_gemba if x["severity"] == "minor"]))
    statistics_collector["esaai"]["segment_count_minor"].append(len([x for x in spans_esaai if x["severity"] == "minor"]))
    statistics_collector["esa"]["segment_count_minor"].append(len([x for x in spans_esa if x["severity"] == "minor"]))
    statistics_collector["mqm"]["segment_count_minor"].append(len([x for x in spans_mqm if x["severity"] == "minor"]))
    statistics_collector["wmt"]["segment_count_minor"].append(len([x for x in spans_wmt if x["severity"] == "minor"]))

    statistics_collector["gemba"]["segment_count_major"].append(len([x for x in spans_gemba if x["severity"] == "major"]))
    statistics_collector["esaai"]["segment_count_major"].append(len([x for x in spans_esaai if x["severity"] == "major"]))
    statistics_collector["esa"]["segment_count_major"].append(len([x for x in spans_esa if x["severity"] == "major"]))
    statistics_collector["mqm"]["segment_count_major"].append(len([x for x in spans_mqm if x["severity"] in {"major", "critical"}]))
    statistics_collector["wmt"]["segment_count_major"].append(len([x for x in spans_wmt if x["severity"] in {"major", "critical"}]))

    statistics_collector["esaai"]["score"].append(row["ESAAI-1_score"])
    statistics_collector["esa"]["score"].append(row["ESA-1_score"])
    statistics_collector["esaai"]["score_mqm"].append(row["ESAAI-1_score_mqm"])
    statistics_collector["esa"]["score_mqm"].append(row["ESA-1_score_mqm"])
    statistics_collector["mqm"]["score_mqm"].append(row["MQM-1_score"])
    statistics_collector["wmt"]["score_mqm"].append(row["WMT-MQM_score"])

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
    np.array(statistics_collector["esaai"]["segment_count"]),
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
plt.savefig("PAPER_ESAAI/generated_plots/overview_segment_count_esaai.pdf")
plt.show()