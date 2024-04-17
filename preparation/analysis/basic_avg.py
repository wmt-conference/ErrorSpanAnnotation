import csv
import numpy as np
import json

data_mqm = list(csv.reader(open("../ErrorSpanAnnotations/campaign-ruction-rc5/240315rc5MQM.scores.csv")))
data_esa = list(csv.reader(open("../ErrorSpanAnnotations/campaign-ruction-rc5/240315rc5ESA.scores.csv")))
data_gmb = list(csv.reader(open("../ErrorSpanAnnotations/campaign-ruction-rc5/240315rc5GEMBA.scores.csv")))


def print_stats(data):
    aggregation = {"duration": [], "error_count": []}
    for line in data:
        duration = float(line[11])-float(line[10])
        if duration > 1 and duration < 60*30:
            aggregation["duration"].append(duration)

        aggregation["error_count"].append(len(json.loads(line[9])))

    for k, v in aggregation.items():
        print(k, f"{np.average(v):.1f}")

print_stats(data_mqm)
print_stats(data_esa)
print_stats(data_gmb)