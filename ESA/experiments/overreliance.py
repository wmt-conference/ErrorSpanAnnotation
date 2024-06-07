from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["ESAAI-1", "LLM"], only_overlap=False).dropna()
import matplotlib.pyplot as plt
import collections
import ESA.figutils
import numpy as np
ESA.figutils.matplotlib_default()

per_progress = collections.defaultdict(list)
for annotator in df["ESAAI-1_AnnotatorID"].unique():
    df_local = df[df["ESAAI-1_AnnotatorID"] == annotator]
    df_local = df_local.sort_values(by="ESAAI-1_start_time")
    for line_i, (span_gemba, span_esaai) in enumerate(zip(df_local["LLM_error_spans"].tolist(), df_local["ESAAI-1_error_spans"].tolist())):
        span_gemba = {(x["start_i"], x["end_i"]) for x in span_gemba}
        span_esaai = {(x["start_i"], x["end_i"]) for x in span_esaai}

        per_progress[int(line_i*100/len(df_local))].append({
            "span_kept": len(span_gemba & span_esaai),
            "span_removed": len(span_gemba - span_esaai),
            "span_added": len(span_esaai - span_gemba),
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
    width=1.05,
    clip_on=False,
)
plt.bar(
    range(len(per_progress)),
    height=[-user['span_added'] for user in per_progress],
    color=ESA.figutils.COLORS[1],
    label="Added",
    width=1.05,
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
plt.ylim(-1.8, 2.0)
plt.gca().spines[["top", "right"]].set_visible(False)

plt.tight_layout(pad=0.1)
plt.savefig("PAPER_ESAAI/generated_plots/overreliance.pdf")
plt.show()