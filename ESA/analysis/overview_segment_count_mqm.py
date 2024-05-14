import json
import numpy as np
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import collections

df = MergedAnnotations().df


statistics_collector = {
    schema: collections.defaultdict(list)
    for schema in ["esa", "gesa", "gemba", "mqm"]
}

# Index(['login_mqm', 'system', 'itemID', 'is_bad', 'source_lang', 'target_lang',
#        'score_mqm', 'documentID', 'span_errors_mqm', 'start_time_mqm',
#        'end_time_mqm', 'duration_seconds_mqm', 'AnnotatorID_mqm',
#        'valid_segment', 'source_seg', 'translation_seg', 'login_esa',
#        'score_esa', 'span_errors_esa', 'start_time_esa', 'end_time_esa',
#        'duration_seconds_esa', 'AnnotatorID_esa', 'login_gemba', 'score_gemba',
#        'span_errors_gemba', 'start_time_gemba', 'end_time_gemba',
#        'duration_seconds_gemba', 'AnnotatorID_gemba',
#        'gemba_mqm_span_errors_gemba'],
#       dtype='object')
for _, row in df.iterrows():
    if type(row["gemba_mqm_span_errors_gemba"]) != list:
        continue
    span_errors_esa = json.loads(row["span_errors_esa"])
    span_errors_mqm = json.loads(row["span_errors_mqm"])

    statistics_collector["esa"]["segment_count"].append(len(span_errors_esa))
    statistics_collector["mqm"]["segment_count"].append(len(span_errors_mqm))

    statistics_collector["esa"]["segment_count_minor"].append(len([x for x in span_errors_esa if x["severity"] == "minor"]))
    statistics_collector["mqm"]["segment_count_minor"].append(len([x for x in span_errors_mqm if x["severity"] == "minor"]))

    statistics_collector["esa"]["segment_count_major"].append(len([x for x in span_errors_esa if x["severity"] == "major"]))
    statistics_collector["mqm"]["segment_count_major"].append(len([x for x in span_errors_mqm if x["severity"] in {"major", "critical"}]))

    statistics_collector["esa"]["score"].append(row["score_esa"])
    statistics_collector["esa"]["score"].append(row["score_mqm"])

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
    "width": 0.3,
}
BINS_BASE = np.linspace(1, 6, 6)

OFFSET_X = 0.3

ROW_COUNT = len(statistics_collector["esa"]["segment_count_minor"])

# TODO: major/minor
bins_y, _, _ = plt.hist(
    np.array(statistics_collector["esa"]["segment_count_major"])-OFFSET_X,
    label="ESA Major",
    bins=BINS_BASE-OFFSET_X,
    color=figutils.COLORS[0],
    alpha=0.8,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)
plt.hist(
    np.array(statistics_collector["esa"]["segment_count_minor"])-OFFSET_X,
    label="ESA Minor",
    color=figutils.COLORS[0],
    alpha=0.3,
    bottom=bins_y,
    bins=BINS_BASE-OFFSET_X,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)
bins_y, _, _ = plt.hist(
    np.array(statistics_collector["mqm"]["segment_count_major"]),
    label="MQM Major",
    color=figutils.COLORS[1],
    alpha=0.8,
    bins=BINS_BASE,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)
plt.hist(
    np.array(statistics_collector["mqm"]["segment_count_minor"]),
    label="MQM Minor",
    color=figutils.COLORS[1],
    alpha=0.3,
    bottom=bins_y,
    bins=BINS_BASE,
    weights=[1 / ROW_COUNT for _ in range(ROW_COUNT)],
    **KWARGS
)

plt.gca().spines[['top', 'right']].set_visible(False)
plt.legend()
plt.xlim(None, 4.5)
# plt.xticks([0, 1, 2, 3, 4])
plt.yticks([0, 0.2], ["0%", "20%"])

plt.xlabel("Error span count", labelpad=-2)
plt.ylabel("Frequency" + " "*5, labelpad=-10)
plt.tight_layout(pad=0)
plt.savefig("figures/overview_segment_count_mqm.pdf")
plt.show()