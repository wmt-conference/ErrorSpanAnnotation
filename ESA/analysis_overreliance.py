import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import matplotlib.pyplot as plt
import json
import collections
import ESA.figutils
import numpy as np
ESA.figutils.matplotlib_default()

df = MergedAnnotations().df


per_progress = collections.defaultdict(list)
for annotator in df.AnnotatorID_gemba.unique():
    df_local = df[df.AnnotatorID_gemba == annotator]
    df_local = df_local.sort_values(by="start_time_gemba")
    for line_i, (span_gemba, span_gesa) in enumerate(zip(df_local.gemba_mqm_span_errors_gemba.tolist(), df_local.span_errors_gemba.tolist())):
        if type(span_gemba) != list:
            continue
        span_gemba = span_gemba
        span_gesa = json.loads(span_gesa)
        span_gemba = {(x["start_i"], x["end_i"]) for x in span_gemba}
        span_gesa = {(x["start_i"], x["end_i"]) for x in span_gesa}

        per_progress[int(line_i*100/len(df_local))].append({
            "span_kept": len(span_gemba & span_gesa),
            "span_removed": len(span_gemba - span_gesa),
            "span_added": len(span_gesa & span_gemba),
        })

# average across timestamps
per_progress = [
    {
        "span_kept": np.average([x["span_kept"] for x in x_v]),
        "span_removed": np.average([x["span_removed"] for x in x_v]),
        "span_added": np.average([x["span_added"] for x in x_v]),
    }
    for x_v in per_progress.values()
]

plt.figure(figsize=(4, 2))

plt.bar(
    range(len(per_progress)),
    height=[user['span_removed']+user['span_kept'] for user in per_progress],
    color=ESA.figutils.COLORS[0],
    label="Removed",
    width=0.95,
    clip_on=False,
)
plt.bar(
    range(len(per_progress)),
    height=[user['span_kept'] for user in per_progress],
    color=ESA.figutils.COLORS[3],
    label="Kept",
    width=1,
    clip_on=False,
)
plt.bar(
    range(len(per_progress)),
    height=[-user['span_added'] for user in per_progress],
    color=ESA.figutils.COLORS[1],
    label="Added",
    width=1,
    clip_on=False,
)

plt.xticks(
    [0, 20, 80, 100],
    ["0%", "20%", "80%", "100%"],
)
plt.xlabel("Annotation progress", labelpad=-8)
plt.yticks([-1, 0, 1], ["+1", "0", "+1"])
plt.ylabel("Segments")


plt.legend(
    facecolor="#ccc",
    handlelength=0.5,
    ncols=3,
    columnspacing=0.5,
    loc="lower center",
)
plt.ylim(-2.2, 2.0)
plt.gca().spines[["top", "right"]].set_visible(False)

plt.tight_layout(pad=0.1)
plt.savefig("figures/overreliance.pdf")
plt.show()