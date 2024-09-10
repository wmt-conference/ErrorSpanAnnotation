import json
import glob
import os
import collections
import random
import numpy as np
import itertools
import csv
import matplotlib.pyplot as plt

data_all = [
    {**line, "wave": wave}
    for wave in range(1, 4)
    for line in list(csv.DictReader(
        open(f"data/wmt24_general/humeval/wave{wave}.csv", "r"),
        fieldnames=["uid", "system", "itemID", "type", "lang1", "lang2", "score", "doc", "unk", "esa", "time_start", "time_end"]
    ))
]
data_all = [
    line for line in data_all
    if "tutorial" not in line["doc"]
]
for line in data_all:
    line["esa"] = json.loads(line["esa"])

data_all_tgt = {}
data_all_bad = {}
for line in data_all:
    key = (
        line["doc"].removesuffix("#bad"),
        line["uid"],
        line["itemID"],
        line["wave"],
    )
    if line["type"] == "BAD":
        data_all_bad[key] = line
    elif line["type"] == "TGT":
        data_all_tgt[key] = line

bad_less_tgt = []
for key, line_bad in data_all_bad.items():
    if key not in data_all_tgt:
        continue
    line_tgt = data_all_tgt[key]
    bad_less_tgt.append(float(line_tgt["score"]) > float(line_bad["score"]))

print(np.average(bad_less_tgt))