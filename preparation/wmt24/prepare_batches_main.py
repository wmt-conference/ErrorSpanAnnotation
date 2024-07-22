import argparse
import json
import glob
import os
import collections
import random
import itertools
import copy
import quality_control


LANG_2_TO_3 = {
    "en": "eng",
    "de": "deu",
    "cs": "ces",
    "hr": "hrv",
    "pl": "plk",
    "ru": "rus",
    "zh": "zho",
}

args = argparse.ArgumentParser()
args.add_argument("--langs", default="en-de")
args.add_argument("--wave", type=int, default=0)
args = args.parse_args()

SEC_TUTORIAL = json.load(open(f"data/tutorial/de-en.esa.json", "r"))
SYSTEMS = json.load(open(f"data/wmt24_general/systems.json", "r"))[args.langs]
SYSTEMS = [
    sys.replace("IOL-Research", "IOL_Research")
    for sys in SYSTEMS if sys != "tutorial"
]
BAD_COUNT = 12


def load_tsv(filename: str, tsv_index: None | int = None):
    data = open(filename, "r").readlines()

    # all files should start with canary
    assert data[0].split()[0].lower() == "canary", data[0]
    data = data[1:]

    data = [x.strip("\n") for x in data]

    if tsv_index is not None:
        data = [x.split("\t")[tsv_index] for x in data]

    return data


lines_src = load_tsv(f"data/wmt24_general/sources/{args.langs}.txt")
lines_doc = load_tsv(
    f"data/wmt24_general/documents/{args.langs}.docs",
    tsv_index=1
)
lines_domain = load_tsv(
    f"data/wmt24_general/documents/{args.langs}.docs",
    tsv_index=0
)

# trim documents to first 10
doc_counter = collections.Counter()
for line_i, line in enumerate(lines_doc):
    if doc_counter[line] >= 10:
        lines_doc[line_i] = None
    doc_counter[line] += 1

# Python supports this!
assert len(lines_src) == len(lines_doc) == len(lines_domain)

# load systems and references
lines_systems = {
    sys: load_tsv(f"data/wmt24_general/system-outputs/{args.langs}/{sys}.txt")
    for sys in SYSTEMS
}
references = [
    os.path.basename(f).removesuffix(".txt").removeprefix(f"{args.langs}.")
    for f in glob.glob(f"data/wmt24_general/references/{args.langs}.*.txt")
]
lines_systems |= {
    ref: load_tsv(f"data/wmt24_general/references/{args.langs}.{ref}.txt")
    for ref in references
}
# treat references as systems from now on
SYSTEMS += references
del references

assert all(len(lines_systems[system]) == len(lines_src) for system in SYSTEMS)

# we need stable ordering of docs
docs = set(lines_doc)
docs.remove(None)
docs = list(docs)
docs.sort()
random.Random(0).shuffle(docs)

doc_line_count = collections.Counter(lines_doc)
doc_line_count.pop(None)

# take first or second part based on the wave
docs = docs[args.wave*len(docs)//2:(args.wave+1)*len(docs)//2]
docs = list(set(docs))
docs.sort()
random.Random(0).shuffle(docs)

# count words/lines in documents
doc_word_count = collections.Counter()
for doc, line_src in zip(lines_doc, lines_src):
    doc_word_count[doc] += len(line_src.split())

print(
    f"DOCS ({len(docs)}, "
    f"{sum([doc_line_count[doc] for doc in docs])} lines) in wave {args.wave}:",
    docs
)

# try to balance document lengths (words)
sys_docs = list(itertools.product(docs, SYSTEMS))
sys_docs.sort(key=lambda x: doc_word_count[x[0]])
sys_docs_long = sys_docs[:len(sys_docs)//2]
sys_docs_short = sys_docs[len(sys_docs)//2:]
# shuffle only within the length bucket
r = random.Random(0)
r.shuffle(sys_docs_long)
r.shuffle(sys_docs_short)

# intervewave the documents
# should be one short, one long, etc..
docs_queue = sys_docs_short + sys_docs_long
docs_queue[0::2] = sys_docs_short
docs_queue[1::2] = sys_docs_long

print(sorted(list(doc_line_count.values())))

print(f"SYSTEMS ({len(SYSTEMS)})")
print(
    f"DOC+SYSTEMS ({len(docs_queue)} sysdocs, "
    f"{sum([doc_line_count[doc] for doc, sys in docs_queue if doc in docs])} total lines)"
)

tasks = []
R_DOC_FILLING = random.Random(0)
R_DOC_SHUFFLING = random.Random(0)
while docs_queue:
    task_docs = [copy.deepcopy(SEC_TUTORIAL)]
    def task_docs_len(): return sum([len(l) for l in task_docs])

    def task_qc_len(): return sum(
        [len([x for x in l if x["itemType"] == "BAD"]) for l in task_docs])

    while task_docs_len() < 100 - BAD_COUNT:
        # we ran out of documents to distribute
        if not docs_queue:
            duplicate_i = 0

            # sample new doc (not tutorial, not QC --- can't be because they're added later)
            # blocks the same doc from being dupped twice?
            task_docs_available = copy.deepcopy(task_docs[1:])
            R_DOC_FILLING.shuffle(task_docs_available)

            while task_docs_len() < 100 - BAD_COUNT:
                doc_new = task_docs_available.pop(0)
                # trim it if it's too much
                doc_new = doc_new[:100 - BAD_COUNT - task_docs_len()]
                for line in doc_new:
                    line["documentID"] = f"{line['documentID']}#dup"
                duplicate_i += 1
                task_docs.append(doc_new)
                # could happen that we need to duplicate a duplication
                # luckily the document ID would now be #dup#dup
                task_docs_available.append(copy.deepcopy(doc_new))

            # end the filling phase
            break

        # if the next document would be too much then just trim it
        if doc_line_count[docs_queue[0][0]] + task_docs_len() > 100 - BAD_COUNT:
            doc, system = docs_queue[0]
            lines_i = [i for i, line in enumerate(lines_doc) if line == doc]
            item_lines_src = [lines_src[i] for i in lines_i]
            item_lines_tgt = [lines_systems[system][i] for i in lines_i]
            task_docs.append([
                {
                    "mqm": [],
                    "documentID": doc + "#incomplete",
                    "sourceText": line_src,
                    "targetText": line_tgt,
                    "itemType": "TGT",
                    "sourceID": f"{line_i}#{args.langs}",
                    "targetID": f"{line_i}#{system}",
                    "itemID": line_i,
                    # will pop
                    "_is_speech": lines_domain[lines_i[0]] == "speech",
                }
                for line_i, line_src, line_tgt in zip(lines_i, item_lines_src, item_lines_tgt)
            ][:100-BAD_COUNT-task_docs_len()])
            # end the filling phase
            break

        doc, system = docs_queue.pop(0)
        lines_i = [i for i, line in enumerate(lines_doc) if line == doc]
        item_lines_src = [lines_src[i] for i in lines_i]
        item_lines_tgt = [lines_systems[system][i] for i in lines_i]
        task_docs.append([
            {
                "mqm": [],
                "documentID": doc,
                "sourceText": line_src,
                "targetText": line_tgt,
                "itemType": "TGT",
                "sourceID": f"{line_i}#{args.langs}",
                "targetID": f"{line_i}#{system}",
                "itemID": line_i,
                "_is_speech": lines_domain[lines_i[0]] == "speech",  # will pop
            }
            for line_i, line_src, line_tgt in zip(lines_i, item_lines_src, item_lines_tgt)
        ])

    # add quality control
    while task_docs_len() < 100:
        task_docs.append(quality_control.create_bad_document(task_docs))
    # trim the last doc to 100
    task_docs[-1] = task_docs[-1][:100 - (task_docs_len()-len(task_docs[-1]))]

    # final shuffle all docs except for tutorial
    task_docs = [task_docs[0]] + \
        R_DOC_SHUFFLING.sample(task_docs[1:], len(task_docs[1:]))

    items = []
    for item in [x for l in task_docs for x in l]:
        if "_is_speech" in item and item.pop("_is_speech"):
            filename = item["documentID"].replace("#dup", "").replace(
                "#incomplete", "").replace("#bad", "")
            filename = "_".join(filename.split("_")[1:])
            item["sourceText"] = f"""
                <video
                    src="https://vilda.net/s/wmt24/{filename}.mp4"
                    controls
                    disablepictureinpicture
                    preload="auto"
                    controlslist="nodownload"
                ></video>
            """
        item["_item"] = ""
        item["isCompleteDocument"] = False

        items.append(item)

    tasks.append({
        "items": items,
        "task": {
            "batchNo": len(tasks)+1,
            "randomSeed": 0,
            "requiredAnnotations": 1,
            "sourceLanguage": LANG_2_TO_3[args.langs.split("-")[0]],
            "targetLanguage": LANG_2_TO_3[args.langs.split("-")[1]],
        }
    })

print("\n".join([
    f"Task {task_i:>3}: "
    f"{len(set([x['documentID'] for x in task['items']])):>4} docs, "
    f"{len(task['items']):>6} lines, "
    f"{sum([len([x for x in task['items'] if x['documentID'].endswith('#bad')])]):>6} BAD lines, "
    f"{sum([len([x for x in task['items'] if x['documentID'].endswith('#incomplete')])]):>6} incomplete doc lines, "
    f"{sum([len([x for x in task['items'] if x['itemType'] == 'TGT' and '#dup' not in x['documentID']])]):>6} unique TGT lines, "
    f"{sum([len(x['sourceText'].split()) for x in task['items']]):>6} words"
    for task_i, task in enumerate(tasks)
]))

json.dump(
    tasks,
    open(f"data/wmt24_general/batches_wave{args.wave}.{args.langs}.json", "w"),
    indent=2,
)
