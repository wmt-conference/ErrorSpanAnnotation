import collections
import scipy.stats
import matplotlib.pyplot as plt
import ESA.figutils
from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "MQM-1", "ESA-2"], only_overlap=False).dropna()
ESA.figutils.matplotlib_default()


def featurize_line(item, protocol):
    return (
        item["sourceID"],
        item[f"ESA-1_score"],
    ), (
        len([x for x in item[f"{protocol}_error_spans"] if x["severity"] == "minor"]),
        len([x for x in item[f"{protocol}_error_spans"] if x["severity"] == "major"]),
        len([x for x in item[f"{protocol}_error_spans"] if x["end_i"] == "missing"]),
    )


# compute model performance
# -------------------------
data_raw = [featurize_line(r, "ESA-1") for _, r in df.iterrows()]
data = collections.defaultdict(list)
for item in data_raw:
    data[item[0][0]].append((item[1], item[0][1]))
data = list(data.values())

data_true = [x[1] for l in data for x in l]
prev_max = None
corrs = []
for fv in range(0, 100+1, 1):
    fv = fv / 10
    def predict_mqm_like_custom(spans):
        return -sum([{"minor": 1, "major": fv, "undecided": 0}[x["severity"]] for x in spans])
    data_pred_lr = [predict_mqm_like_custom(r["ESA-1_error_spans"]) for _, r in df.iterrows()]
    corr = scipy.stats.pearsonr(data_pred_lr, data_true)[0]
    if prev_max is None or corr > prev_max:
        print(f"1-{fv:0>4}->ESA1: {corr:.8f} *")
        prev_max = corr
    else:
        print(f"1-{fv:0>4}->ESA1: {corr:.8f}")
    corrs.append(corr)


plt.figure(figsize=(3, 2))
plt.plot(corrs, color="black")
plt.xticks([0, 50,100], [0, 5, 10])
plt.vlines(x=50, ymin=min(corrs), ymax=corrs[50], color=ESA.figutils.COLORS[0])
plt.vlines(x=48, ymin=min(corrs), ymax=corrs[48], color=ESA.figutils.COLORS[2])
plt.text(30, 0.3, "Optimal\nx=4.8", ha="center", color=ESA.figutils.COLORS[2])
plt.text(70, 0.3, "Default\nx=5", ha="center", color=ESA.figutils.COLORS[0])
plt.ylabel("Correlation")
plt.xlabel("minor: -1, major: -$x$ error weights")
plt.tight_layout()
plt.savefig("PAPER_ESA/generated_plots/predicting_score.pdf")
plt.show()


# compute feature importance
# --------------------------
data_tgt = [r["ESA-1_score"] for _, r in df.iterrows()]
FEATURES = [
    ("Source token count", lambda r: len(r["source"].split())),
    ("Target token count", lambda r: len(r["hypothesis"].split())),
    ("break", None),
    ("Minor error count", lambda r: len([x for x in r[f"ESA-1_error_spans"] if x["severity"] == "minor"])),
    ("Major error count", lambda r: len([x for x in r[f"ESA-1_error_spans"] if x["severity"] == "major"])),
    ("Missing error count", lambda r: len([x for x in r[f"ESA-1_error_spans"] if x["end_i"] == "missing"])),
    ("break", None),
    ("Minor error count (normalized)", lambda r: len([x for x in r[f"ESA-1_error_spans"] if x["severity"] == "minor"])/len(r["hypothesis"].split())),
    ("Major error count (normalized)", lambda r: len([x for x in r[f"ESA-1_error_spans"] if x["severity"] == "major"])/len(r["hypothesis"].split())),
    ("Missing error count (normalized)", lambda r: len([x for x in r[f"ESA-1_error_spans"] if x["end_i"] == "missing"])/len(r["hypothesis"].split())),
]

for feature_name, feature_func in FEATURES:
    if feature_name == "break":
        print(r"\\[-0.5em]")
        continue
    data_feature = [feature_func(r) for _, r in df.iterrows()]
    print(
        feature_name,
        f"{scipy.stats.pearsonr(data_feature, data_tgt)[0]:.2f}",
        sep=" & ", end="\\\\\n"
    )