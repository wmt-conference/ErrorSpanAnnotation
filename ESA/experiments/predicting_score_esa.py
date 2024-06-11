import collections
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
import ESA.figutils
from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "MQM-1", "ESA-2"], only_overlap=False).dropna()
ESA.figutils.matplotlib_default()

# compute model performance
# -------------------------
data_true = [r["ESA-1_score"] for _, r in df.iterrows()]
prev_max = None
corrs = []
for fv in range(0, 100+1, 1):
    fv = fv / 10
    def predict_mqm_like_custom(item):
        return -sum([{"minor": 1, "major": fv, "undecided": 0}[x["severity"]] for x in item["ESA-1_error_spans"]])/len(item["hypothesis"].split())
    data_pred_lr = [predict_mqm_like_custom(r) for _, r in df.iterrows()]
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

# compute system-level correlation
data_sys_true = collections.defaultdict(list)
data_sys_plain = collections.defaultdict(list)
data_sys_normalized = collections.defaultdict(list)
def predict_mqm_like_plain(item):
        return -sum([{"minor": 1, "major": 5, "undecided": 0}[x["severity"]] for x in item["ESA-1_error_spans"]])
def predict_mqm_like_normalized(item):
        return -sum([{"minor": 1, "major": 5, "undecided": 0}[x["severity"]] for x in item["ESA-1_error_spans"]])/len(item["hypothesis"].split())
for _, r in df.iterrows():
    data_sys_true[r["systemID"]].append(r["ESA-1_score"])
    data_sys_plain[r["systemID"]].append(predict_mqm_like_plain(r))
    data_sys_normalized[r["systemID"]].append(predict_mqm_like_normalized(r))

data_sys_true = {k: np.average(v) for k, v in data_sys_true.items()}
data_sys_plain = {k: np.average(v) for k, v in data_sys_plain.items()}
data_sys_normalized = {k: np.average(v) for k, v in data_sys_normalized.items()}
assert data_sys_true.keys() == data_sys_plain.keys()
print("Plain     ", f"{scipy.stats.spearmanr(list(data_sys_true.values()), list(data_sys_plain.values()))[0]:.4f}")
print("Normalized", f"{scipy.stats.spearmanr(list(data_sys_true.values()), list(data_sys_normalized.values()))[0]:.4f}")



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