# wget https://storage.googleapis.com/mt-metrics-eval/mt-metrics-eval-v2.tgz
# and put it in data

import collections
import json
import numpy as np

data_mqm = collections.defaultdict(list)

for line in open("data/mt-metrics-eval-v2/wmt23.sent/human-scores/en-de.mqm.merged.seg.rating", "r"):
    sys, mqm = line.strip().split("\t")
    if mqm == "None":
        mqm = []
    else:
        mqm = json.loads(mqm)["errors"]
    mqm = [
        {
            "start_i": x["start"],
            "end_i": x["end"],
            "severity": x["severity"],
        }
        for x in mqm
    ]
    data_mqm[sys].append({"mqm": mqm})

sources = [
    x.strip() for x in
    open("data/mt-metrics-eval-v2/wmt23.sent/sources/en-de.txt", "r")
]

source = sources[:100]

measurements = collections.defaultdict(list)

SEVERITY_TO_SCORE = {
    "minor": -1,
    "major": -5,
    "critical": -25,
    "neutral": 0,
}
def segment_mqm_score(mqm):
    return sum(
        SEVERITY_TO_SCORE[x["severity"]]
        for x in mqm
    )

for sys in data_mqm.keys():
    targets = [
        x.strip() for x in
        open(
            f"data/mt-metrics-eval-v2/wmt23.sent/system-outputs/en-de/{sys}.txt", "r")
    ]
    for obj, target, source in zip(data_mqm[sys], targets, sources):
        obj["sourceText"] = source
        obj["targetText"] = target

        measurements["tgt_len"].append(len(target.split()))
        measurements["src_len"].append(len(source.split()))

        measurements["mqm_is"].append(len(obj["mqm"]) != 0)
        measurements["mqm_count"].append(len(obj["mqm"]))
        if obj["mqm"]:
            measurements["mqm_count_nonzero"].append(len(obj["mqm"]))
            measurements["segment_mqm_score_nonzero"].append(segment_mqm_score(obj["mqm"]))
            measurements["sev_major"].append(len([x for x in obj["mqm"] if x["severity"] == "major"]))
            measurements["sev_minor"].append(len([x for x in obj["mqm"] if x["severity"] == "minor"]))


        measurements["sev_critical_SUM"].append(len([x for x in obj["mqm"] if x["severity"] == "critical"]))
        measurements["sev_neutral_SUM"].append(len([x for x in obj["mqm"] if x["severity"] == "neutral"]))
        measurements["segment_mqm_score"].append(segment_mqm_score(obj["mqm"]))


for key, values in measurements.items():
    if "SUM" not in key:
        print(key, f"{np.average(values)}")
    else:
        print(key, f"{np.sum(values)}")
