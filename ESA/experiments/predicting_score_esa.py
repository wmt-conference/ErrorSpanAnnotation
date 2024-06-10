import collections
import numpy as np
import scipy.stats
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression, HuberRegressor
from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(
    ["LLM", "ESA-1", "MQM-1", "ESA-2"], only_overlap=False).dropna()


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
data_pred_15 = [r["ESA-1_score_mqm"] for _, r in df.iterrows()]
data_pred_lr = []
for i in range(len(data)):
    data_test = data[i]
    data_train = data[:i] + data[i+1:]
    data_train = [x for l in data_train for x in l]
     
    model = LinearRegression()
    model.fit([x[0] for x in data_train], [x[1] for x in data_train])
    data_pred_lr += list(model.predict([x[0] for x in data_test]))

print("ESA1-learned->ESA1:", scipy.stats.pearsonr(data_pred_lr, data_true)[0])
print("ESA1-MQM->ESA1    :", scipy.stats.pearsonr(data_pred_15, data_true)[0])

# compute coefficients
model = LinearRegression()
model.fit([x[0] for l in data for x in l], data_true)
print(list(zip(["minor", "major", "missing"], model.coef_)))


data_raw = [featurize_line(r, "MQM-1") for _, r in df.iterrows()]
data = collections.defaultdict(list)
for item in data_raw:
    data[item[0][0]].append((item[1], item[0][1]))
data = list(data.values())

data_true = [x[1] for l in data for x in l]
data_pred_15 = [r["MQM-1_score"] for _, r in df.iterrows()]
data_pred_lr = []
for i in range(len(data)):
    data_test = data[i]
    data_train = data[:i] + data[i+1:]
    data_train = [x for l in data_train for x in l]
     
    model = LinearRegression()
    model.fit([x[0] for x in data_train], [x[1] for x in data_train])
    data_pred_lr += list(model.predict([x[0] for x in data_test]))


print("MQM1-learned->ESA1:", scipy.stats.pearsonr(data_pred_lr, data_true)[0])
print("MQM1-MQM->ESA1    :", scipy.stats.pearsonr(data_pred_15, data_true)[0])


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