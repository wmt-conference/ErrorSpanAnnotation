import collections
import json
import random
import argparse
import copy
import glob
import utils
import os

args = argparse.ArgumentParser()
args.add_argument("--sec-tutorial", default="de-en.mqm")
args.add_argument("--bad-segments", type=int, default=12)
args.add_argument("--mqm", default=None)
# for cases where we want to load MQM for filtering but not actually add it
args.add_argument("--mqm-filter", default=None)
args.add_argument("--year", default="wmt23")
args.add_argument("--langs", default="en-de")
args.add_argument("--systems", nargs="+", default=None)
# Appraise section is "exactly" 100 segments
args.add_argument("--src-docs", type=int, default=20)
args.add_argument("--src-docs-seed", type=int, default=0)
args.add_argument("--redundancy", type=int, default=1)
args.add_argument("--suffix", default="")
args = args.parse_args()


def find_file(filename):
    if os.path.exists("data/mt-metrics-eval-v2-custom/" + filename):
        return "data/mt-metrics-eval-v2-custom/" + filename
    if os.path.exists("data/mt-metrics-eval-v2/" + filename):
        return "data/mt-metrics-eval-v2/" + filename
    raise Exception("File " + filename + " not found")


if args.sec_tutorial:
    sec_tutorial = json.load(open(f"data/extra/tutorial-{args.sec_tutorial}.json", "r"))
else:
    sec_tutorial = []

banlines = set()
sources = [
    x.strip() for x in open(find_file(f"{args.year}/sources/{args.langs}.txt"), "r")
]
for line_i, line in enumerate(sources):
    if len(line.split(" ")) > 200:
        banlines.add(line_i)
print("Found", len(banlines), "very long lines, omitting them")
documents = [
    x.strip().split("\t")[1]
    for x in open(find_file(f"{args.year}/documents/{args.langs}.docs"), "r")
]
print(len(sources), "sources")

documents_allowed = random.Random(args.src_docs_seed).sample(sorted(set(documents)), k=args.src_docs)
print(f"Out of {len(set(documents))} chosing the following:", documents_allowed)

data_mqm = collections.defaultdict(list)
if args.mqm:
    for line in open(
        find_file(f"{args.year}/{args.mqm}.seg.rating"),
        "r",
    ):
        sys, mqm = line.strip().split("\t")
        if (args.systems and sys not in args.systems) or sys == "synthetic_ref":
            continue
        if mqm == "None":
            # set to empty MQM
            mqm = []
        else:
            mqm = json.loads(mqm)
            # Tom/Gemba does not provide the same format but that's fine
            if "errors" in mqm:
                mqm = mqm["errors"]
            mqm = [
                {
                    "start_i": x["start"] if x["start"] != -1 else "missing",
                    "end_i": x["end"] if x["end"] != -1 else "missing",
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

# sort for stability and reproducibility
systems.sort()

# filter MQMs globally
data_mqm_filter = collections.defaultdict(list)
if args.mqm_filter:
    for line in open(
        find_file(f"{args.year}/{args.mqm_filter}.seg.rating"),
        "r",
    ):
        sys, mqm = line.strip().split("\t")
        if (args.systems and sys not in args.systems) or sys == "synthetic_ref":
            continue
        if mqm == "None":
            # the length of this list is also the line position
            banlines.add(len(data_mqm_filter[sys]))
        data_mqm_filter[sys].append(None)

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
        obj["itemType"] = "TGT"
        obj["_item"] = f"{sys} | {seg_i} | {document}"

# make sure that we have as many sources as all systems
assert all([len(v) == len(sources) for v in data_mqm.values()])

# filter undesired docs
data_mqm = {
    sys:[obj for obj in data_mqm[sys] if obj["documentID"].split("#")[0] in documents_allowed]
    for sys in systems
}
# filter lines with None MQM
data_mqm = {
    sys:[obj for obj_i, obj in enumerate(data_mqm[sys]) if obj_i not in banlines]
    for sys in systems
}

# throw away sys source structure (transpose)
data_mqm = [list(sublist) for sublist in list(zip(*data_mqm.values()))]
total_lines = len(data_mqm)
print("Skipping", len(banlines), "lines because they are very long or their MQM is None")

# base section is ~100 (safe for the tutorial)
# in case we have 1 task per section, then a single task has to capture all systems
EFFECTIVE_SECTION_SIZE = 100 - len(sec_tutorial) - args.bad_segments

r = random.Random(123)

# shuffle everything on doc level
data_mqm = [obj for syslines in data_mqm for obj in syslines]
data_mqm_doc = collections.defaultdict(list)
for obj in data_mqm:
    data_mqm_doc[obj["documentID"]].append(obj)
data_mqm_doc = list(data_mqm_doc.values())
r.shuffle(data_mqm_doc)
data_mqm = [obj for doc in data_mqm_doc for obj in doc]

tasks = []
print()
while data_mqm:
    data_local = data_mqm[:EFFECTIVE_SECTION_SIZE]
    data_mqm = data_mqm[EFFECTIVE_SECTION_SIZE:]

    while data_local:
        # each Appraise section is strictly 100 segments
        task = data_local[: EFFECTIVE_SECTION_SIZE]
        data_local = data_local[EFFECTIVE_SECTION_SIZE:]

        # prepare bad documents from the global pool
        data_bad = utils.sample_bad_documents(task, args.bad_segments)
        task = copy.deepcopy(data_bad) + task
      
        # shuffle documents on document level
        task_doc = collections.defaultdict(list)
        for item in task:
            task_doc[item["documentID"]].append(item)
        task_doc = list(task_doc.values())
        r.shuffle(task_doc)
        # flatten
        task = [item for doc in task_doc for item in doc]

        # add tutorial to the front
        task = copy.deepcopy(sec_tutorial) + task
        # if we are missing samples, fill them from the beginning
        # but skip the tutorial, which would mess it up
        _duplicate_i = 0
        if len(task) == 100:
            print("Task already", len(task))
        while len(task) < 100:
            _duplicate_i += 1
            _prev_task_len = len(task)
            task_addition = copy.deepcopy(task[len(sec_tutorial):][:100-len(task)])
            for item in task_addition:
                item["documentID"] += f"#duplicate{_duplicate_i}"
            task = task + task_addition
            print(f"{'-' if _duplicate_i > 1 else ''}Filling task from", _prev_task_len, "to", len(task))


        print("Task contains", len({obj["documentID"] for obj in task}), "documents")
        tasks.append(task)
print()

tasks_new = []
for task in tasks:
    # make sure that documents are together
    for obj_i, obj in enumerate(task):
        # Appraise needs positive integer
        obj["itemID"] = obj_i+1
        # mandatory for Appraise backward compatibility
        obj["isCompleteDocument"] = False

    tasks_new.append(task)

print(
    "Created",
    len(tasks),
    "tasks because we have",
    len(systems),
    "systems and",
    args.src_docs,
    "source documents"
)
print(
    "Therefore, each task covers",
    EFFECTIVE_SECTION_SIZE,
    "segments",
    "and contains a tutorial of size",
    len(sec_tutorial),
    "and attention check of size",
    args.bad_segments,
)
print(
    "As a result, we covered",
    total_lines,
    "segments"
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
