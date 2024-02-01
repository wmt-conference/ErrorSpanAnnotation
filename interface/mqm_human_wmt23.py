# wget https://storage.googleapis.com/mt-metrics-eval/mt-metrics-eval-v2.tgz
# and put it in data

import collections
import json
import random
import math

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

queue_all = []


print(len(sources), "sources")
for sys in data_mqm.keys():
    if sys not in {"ONLINE-B"}:
        continue
    print(len(data_mqm[sys]), "of", sys)
    targets = [
        x.strip() for x in
        open(f"data/mt-metrics-eval-v2/wmt23.sent/system-outputs/en-de/{sys}.txt", "r")
    ]
    _obj_i_hack = 0
    for obj_i, (obj, target, source) in enumerate(zip(data_mqm[sys], targets, sources)):
        if not obj["mqm"]:
            continue
        if _obj_i_hack == 100:
            break
        obj["sourceID"] = "wmt23.sent"
        obj["targetID"] = f"wmt23.sent.{sys}"
        # TODO: unsure what this does exactly
        obj["itemType"] = "TGT" if sys != "refA" else "REF"
        obj["sourceText"] = source
        obj["targetText"] = target
        obj["itemID"] = _obj_i_hack
        _obj_i_hack += 1
    
        queue_all.append(obj)

random.Random(123456).shuffle(queue_all)

_block = 0
for obj_i, obj in enumerate(queue_all):
    obj["_item"] = obj_i
    # TODO: unsure what this does exactly
    obj["_block"] = _block//10
    _block += 1


dump_obj = [{
    "items": queue_all,
    "task": {
      "batchNo": 1,
      "batchSize": math.ceil(_block/10),
      "randomSeed": 123456,
      "requiredAnnotations": 1,
      "sourceLanguage": "eng",
      "targetLanguage": "deu"
    }
}]

json.dump(dump_obj, open("data/batches.json", "w"), indent=2)