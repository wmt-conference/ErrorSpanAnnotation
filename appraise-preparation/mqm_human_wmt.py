import collections
import json
import random
import argparse
import copy
import glob
import utils
import os

args = argparse.ArgumentParser()
args.add_argument("--tutorial", default="en-de")
args.add_argument("--mqm", default=None)
args.add_argument("--year", default="wmt23")
args.add_argument("--langs", default="en-de")
args.add_argument("--systems", nargs="+", default=None)
# Appraise section is "exactly" 100 segments
args.add_argument("--sections", type=float, default=1)
args.add_argument("--redundancy", type=int, default=2)
args.add_argument("--suffix", default="")
args = args.parse_args()


def find_file(filename):
    if os.path.exists("data/mt-metrics-eval-v2-custom/" + filename):
        return "data/mt-metrics-eval-v2-custom/" + filename
    if os.path.exists("data/mt-metrics-eval-v2/" + filename):
        return "data/mt-metrics-eval-v2/" + filename
    raise Exception("File " + filename + " not found")


if args.tutorial:
    tutorial = json.load(open(f"data/tutorial/{args.tutorial}.json", "r"))
else:
    tutorial = []

sources = [
    x.strip() for x in open(find_file(f"{args.year}/sources/{args.langs}.txt"), "r")
]
documents = [
    x.strip().split("\t")[1]
    for x in open(find_file(f"{args.year}/documents/{args.langs}.docs"), "r")
]
print(len(sources), "sources")

data_mqm = collections.defaultdict(list)
if args.mqm:
    for line in open(
        find_file(f"{args.year}/{args.mqm}.seg.rating"),
        "r",
    ):
        sys, mqm = line.strip().split("\t")
        if args.systems and sys not in args.systems:
            continue
        if mqm == "None":
            mqm = []
        else:
            mqm = json.loads(mqm)
            # Tom/Gemba does not provide the same format but that's fine
            if "errors" in mqm:
                mqm = mqm["errors"]
        mqm = [
            {
                "start_i": x["start"],
                "end_i": x["end"],
                "severity": x["severity"],
            }
            for x in mqm
        ]
        data_mqm[sys].append({"mqm": mqm})
    systems = list(data_mqm.keys())
else:
    # use any metrics rating to get _item
    _file = glob.glob(f"data/mt-metrics-eval-v2/{args.year}/metric-scores/{args.langs}/*.seg.score")[0]
    for line in open(_file, "r",):
        sys, mqm = line.strip().split("\t")
        if args.systems and sys not in args.systems:
            continue
        data_mqm[sys].append({"mqm": []})
    systems = list(data_mqm.keys())

for sys in systems:
    print(len(data_mqm[sys]), "of", sys)
    targets = [
        x.strip()
        for x in open(
            find_file(f"{args.year}/system-outputs/{args.langs}/{sys}.txt"),
            "r",
        )
    ]
    for seg_i, (obj, target, source, document) in enumerate(
        zip(data_mqm[sys], targets, sources, documents)
    ):
        obj["documentID"] = document+"#"+sys
        obj["sourceID"] = f"{args.year}"
        obj["targetID"] = f"{args.year}.{sys}"
        obj["sourceText"] = source
        obj["targetText"] = target
        obj["_item"] = f"{sys} | {seg_i} | {document}"

# make sure that we have as many sources as all systems
assert all([len(v) == len(sources) for v in data_mqm.values()])

# throw away sys source structure
data_mqm = [[val[i] for val in data_mqm.values()] for i in range(len(sources))]

# base section is ~100 (safe for the tutorial)
# in case we have 1 task per section, then a single task has to capture all systems
EFFECTIVE_SECTION_SIZE = 100 - len(tutorial)
# make sure we don't get messed up by the rounding
assert int(args.sections * EFFECTIVE_SECTION_SIZE) == args.sections * EFFECTIVE_SECTION_SIZE
data_mqm = data_mqm[: int(args.sections * EFFECTIVE_SECTION_SIZE)]

r = random.Random(123)

tasks = []

section_i = 0
while data_mqm:
    section_i += 1
    data_local = data_mqm[:EFFECTIVE_SECTION_SIZE]
    data_local = [
        x for sys_line in data_local for x in sys_line
    ]
    data_mqm = data_mqm[EFFECTIVE_SECTION_SIZE:]
    print("Covering from", (section_i-1)*EFFECTIVE_SECTION_SIZE, "to", section_i*EFFECTIVE_SECTION_SIZE)

    # shuffle everything within the section
    r.shuffle(data_local)

    while data_local:
        # each Appraise section is strictly 100 segments

        # add tutorial to the front
        task = data_local[: EFFECTIVE_SECTION_SIZE]
      
        # shuffle documents on document level
        task_doc = collections.defaultdict(list)
        for item in task:
            task_doc[item["documentID"]].append(item)
        task_doc = list(task_doc.values())
        r.shuffle(task_doc)
        task = [item for doc in task_doc for item in doc]

        task = copy.deepcopy(tutorial) + task
        # if we are missing at most 5 samples, fill them from the beginning
        # but skip the tutorial, which would mess it up
        if len(task) >= 50+len(tutorial) and len(task) < 100:
            print("Aligning from", len(task), "to", 100)
            task_addition = copy.deepcopy(
                task[len(tutorial): 100 - len(task)+len(tutorial)]
            )
            for item in task_addition:
                item["documentID"] += "#duplicate"
            task = task + task_addition

        if len(task) != 100:
            raise Exception("Tried to add a task without exactly 100 segments")
        tasks.append(task)
        data_local = data_local[100 - len(tutorial) :]

tasks_new = []
for task in tasks:
    # make sure that documents are together
    for obj_i, obj in enumerate(task):
        # Appraise needs positive integer
        obj["itemID"] = obj_i+1
        # everything is TGT, though not sure what that means
        obj["itemType"] = "TGT"
        # mandatory for Appraise backward compatibility
        obj["isCompleteDocument"] = False

    tasks_new.append(task)

print(
    "Created",
    len(tasks),
    "tasks because we have",
    len(systems),
    "systems and",
    args.sections,
    "sections"
)
print(
    "Therefore, each task covers",
    EFFECTIVE_SECTION_SIZE,
    "segments",
    "and contains a tutorial of size",
    len(tutorial),
)
print(
    "As a result, we covered the first",
    section_i*EFFECTIVE_SECTION_SIZE,
    "segments",
    "because you requested",
    args.sections,
    "sections",
)


lang1, lang2 = args.langs.split("-")
lang1l, lang2l = utils.LANG_2_TO_3[lang1], utils.LANG_2_TO_3[lang2]
dump_obj = []
for task_i, task in enumerate(tasks_new):
    obj = {
        "items": task,
        "task": {
            "batchNo": task_i + 1,
            "randomSeed": 123456,
            "requiredAnnotations": 1,
            "sourceLanguage": lang1l,
            "targetLanguage": lang2l,
        },
    }
    dump_obj.append(obj)

print("Put this in your manifest:")
print(json.dumps([lang1l, lang2l, "uniform", args.redundancy * len(tasks), len(tasks)]))

json.dump(dump_obj, open(f"data/batches_{args.year}_{args.langs}{args.suffix}.json", "w"), indent=2)
