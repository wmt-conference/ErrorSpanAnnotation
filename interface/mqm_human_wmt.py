# wget https://storage.googleapis.com/mt-metrics-eval/mt-metrics-eval-v2.tgz
# and put it in `data/`

# python3 interface/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --no-mqm --tasks-per-section 1 --systems "ONLINE-Y" "refA"
# python3 interface/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs de-en --no-mqm --tasks-per-section 1 --systems "ONLINE-Y" "refA"
# python3 interface/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --no-mqm --tasks-per-section 1 --systems "ONLINE-Y" "refA"
# python3 interface/mqm_human_wmt.py --year wmt22 --redundancy 20 --langs en-hr --no-mqm --tasks-per-section 1 --systems "Online-A" "refA"
# python3 interface/mqm_human_wmt.py --year wmt20 --redundancy 20 --langs en-pl --no-mqm --tasks-per-section 1 --systems "Online-A.1576" "ref"


import collections
import json
import random
import argparse
import copy
import glob
import utils

args = argparse.ArgumentParser()
args.add_argument("--tutorial", default="en-de")
args.add_argument("--no-mqm", action="store_true")
args.add_argument("--year", default="wmt23")
args.add_argument("--langs", default="en-de")
args.add_argument("--systems", nargs="+", default=None)
# Appraise section is "exactly" 100 segments
args.add_argument("--tasks-per-section", type=int, default=2)
args.add_argument("--sections", type=int, default=1)
args.add_argument("--redundancy", type=int, default=2)
args = args.parse_args()

if args.tutorial:
    tutorial = json.load(open(f"data/tutorial/{args.tutorial}.json", "r"))
else:
    tutorial = []

sources = [
    x.strip() for x in
    open(f"data/mt-metrics-eval-v2/{args.year}/sources/{args.langs}.txt", "r")
]
documents = [
    x.strip().split("\t")[1] for x in
    open(
        f"data/mt-metrics-eval-v2/{args.year}/documents/{args.langs}.docs", "r")
]
print(len(sources), "sources")

data_mqm = collections.defaultdict(list)
if not args.no_mqm:
    for line in open(f"data/mt-metrics-eval-v2/{args.year}/human-scores/{args.langs}.mqm.merged.seg.rating", "r"):
        sys, mqm = line.strip().split("\t")
        if args.systems and sys not in args.systems:
            continue
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
    systems = list(data_mqm.keys())
else:
    systems = [
        sys.removeprefix(
            f"data/mt-metrics-eval-v2/{args.year}/system-outputs/{args.langs}/").removesuffix(".txt")
        for sys in glob.glob(f"data/mt-metrics-eval-v2/{args.year}/system-outputs/{args.langs}/*.txt")
    ]
    systems = [
        sys for sys in systems
        if not args.systems or sys in args.systems
    ]
    data_mqm = {
        sys: [{"mqm": []} for _ in sources]
        for sys in systems
    }

for sys in systems:
    print(len(data_mqm[sys]), "of", sys)
    targets = [
        x.strip()
        for x in open(
            f"data/mt-metrics-eval-v2/{args.year}/system-outputs/{args.langs}/{sys}.txt", "r"
        )
    ]
    for seg_i, (obj, target, source, document) in enumerate(zip(data_mqm[sys], targets, sources, documents)):
        obj["documentID"] = document
        obj["sourceID"] = f"{args.year}"
        obj["targetID"] = f"{args.year}.{sys}"
        obj["sourceText"] = source
        obj["targetText"] = target
        # essentially source ID
        obj["itemID"] = seg_i


# make sure that we have as many sources as all systems
assert all([len(v) == len(sources) for v in data_mqm.values()])

# throw away sys source structure
data_mqm = [
    [val[i] for val in data_mqm.values()]
    for i in range(len(sources))
]

# base section is ~100 (safe for the tutorial)
# in case we have 1 task per section, then a single task has to capture all systems
EFFECTIVE_SECTION_SIZE = (
    (100 - len(tutorial)) *
    args.tasks_per_section // len(systems)
)
data_mqm = data_mqm[:args.sections * EFFECTIVE_SECTION_SIZE]

r = random.Random(123)

tasks = []

for source_section_i in range(len(data_mqm) // EFFECTIVE_SECTION_SIZE):
    source_section_a = EFFECTIVE_SECTION_SIZE * source_section_i
    source_section_b = EFFECTIVE_SECTION_SIZE * (source_section_i + 1)
    data_local = [
        x for sys_line in data_mqm[source_section_a:source_section_b]
        for x in sys_line
    ]
    print("Covering from", source_section_a, "to", source_section_b)

    # shuffle everything within
    r.shuffle(data_local)

    for task_i in range(args.tasks_per_section):
        # each Appraise section is strictly 100 segments

        # add tutorial to the front
        task = copy.deepcopy(tutorial) + data_local[:100 - len(tutorial)]
        # if we are missing at most 5 samples, fill them from the beginning
        if len(task) >= 95:
            task = task + copy.deepcopy(task[:100 - len(task)])
        if len(task) != 100:
            raise Exception("Tried to add a task without exactly 100 segments")
        tasks.append(task)
        data_local = data_local[100 - len(tutorial):]

tasks_new = []
for task in tasks:
    _block = -1
    _cur_doc = None

    for obj_i, obj in enumerate(task):
        if _cur_doc != obj["documentID"]:
            _block += 1
            _cur_doc = obj["documentID"]
        obj["_block"] = _block
        obj["_item"] = obj_i
        # everything is TGT, though not sure what that means
        obj["itemType"] = "TGT"
        # mandatory for Appraise backward compatibility
        obj["isCompleteDocument"] = False

    tasks_new.append(task)

print(
    "Created", len(tasks), "tasks because we have", len(systems), "systems",
    "and you requested", args.tasks_per_section, "tasks per section."
)
print(
    "Therefore, each task covers", EFFECTIVE_SECTION_SIZE, "segments",
    "and contains a tutorial of size", len(tutorial)
)
print(
    "As a result, we covered the first", source_section_b, "segments",
    "because you requested", args.sections, "sections"
)

dump_obj = []
for task_i, task in enumerate(tasks_new):
    obj = {
        "items": task,
        "task": {
            "batchNo": task_i + 1,
            "batchSize": 1,
            "randomSeed": 123456,
            "requiredAnnotations": 1,
            "sourceLanguage": "eng",
            "targetLanguage": "deu"
        }
    }
    dump_obj.append(obj)

lang1, lang2 = args.langs.split("-")
print("Put this in your manifest:")
print(
    json.dumps(
        [
            utils.LANG_2_TO_3[lang1],
            utils.LANG_2_TO_3[lang2],
            "uniform",
            args.redundancy*len(tasks),
            len(tasks)
        ]
    )
)

json.dump(dump_obj, open(
    f"data/batches_{args.year}_{args.langs}.json", "w"), indent=2)
