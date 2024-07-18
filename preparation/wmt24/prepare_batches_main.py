import argparse
import json
import glob
import os
import collections
import random
import itertools
import copy

SEC_TUTORIAL = json.load(open(f"data/tutorial/de-en.esa.json", "r"))

args = argparse.ArgumentParser()
args.add_argument("--langs", default="en-de")
args.add_argument("--wave", type=int, default=0)
args = args.parse_args()


def load_tsv(filename: str, tsv_index: None | int = None):
    data = open(filename, "r").readlines()

    # all files should start with canary
    assert data[0].split()[0].lower()== "canary", data[0]
    data = data[1:]

    data = [x.strip("\n") for x in data]

    if tsv_index:
        data = [x.split("\t")[tsv_index] for x in data]

    return data

lines_src = load_tsv(f"data/wmt24_general/sources/{args.langs}.txt")
lines_doc = load_tsv(f"data/wmt24_general/documents/{args.langs}.docs", tsv_index=1)
lines_domain = load_tsv(f"data/wmt24_general/documents/{args.langs}.docs", tsv_index=0)

# Python supports this!
assert len(lines_src) == len(lines_doc) == len(lines_domain)

# load systems and references
systems = [os.path.basename(f).removesuffix(".txt") for f in glob.glob(f"data/wmt24_general/system-outputs/{args.langs}/*.txt")]
lines_systems = {system: load_tsv(f"data/wmt24_general/system-outputs/{args.langs}/{system}.txt") for system in systems}
references = [os.path.basename(f).removesuffix(".txt").removeprefix(f"{args.langs}.") for f in glob.glob(f"data/wmt24_general/references/{args.langs}.*.txt")]
lines_systems |= {ref: load_tsv(f"data/wmt24_general/references/{args.langs}.{ref}.txt") for ref in references}
# treat references as systems from now on
systems += references
del references

assert all(len(lines_systems[system]) == len(lines_src) for system in systems)

# we need stable ordering of docs
docs = list(set(lines_doc))
docs.sort()
random.Random(0).shuffle(docs)

# take first or second part based on the wave
docs = docs[args.wave*len(docs)//2:(args.wave+1)*len(docs)//2]
doc_word_count = collections.Counter()
for doc, line_src in zip(lines_doc, lines_src):
    doc_word_count[doc] += len(line_src.split())

doc_line_count = collections.Counter(lines_doc)

print(f"DOCS ({len(docs)}) in wave {args.wave}:", docs)

sys_docs = list(itertools.product(docs, systems))
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

print(f"SYSTEMS ({len(systems)})")
print(f"DOC+SYSTEMS ({len(docs_queue)})")

tasks = []
while docs_queue:
    task = []
    task += copy.deepcopy(SEC_TUTORIAL)
    while len(task) < 100:
        if not docs_queue:
            print(f"Unfinished task  but ran out of documents so I'm leaving this task partially unfinished ({len(task)}). TODO")
            # TODO: remove me, this is incorrect
            task = task + task[-(100 - len(task)):]
            break
        
        # TODO: add quality control
        # TODO: handle multimodal (speech domain) differently

        if doc_line_count[docs_queue[0][0]] + len(task) > 100:
            print(f"The next document would be too much so I'm leaving this task partially unfinished ({len(task)}). TODO")
            # TODO: remove me, this is incorrect
            task = task + task[-(100 - len(task)):]
            break

        doc, system = docs_queue.pop(0)
        lines_i = [i for i, line in enumerate(lines_doc) if line == doc]
        item_lines_src = [lines_src[i] for i in lines_i]
        item_lines_tgt = [lines_systems[system][i] for i in lines_i]
        task += [
            {
                "documentID": doc,
                "sourceText": line_src,
                "targetText": line_tgt,
                "TODO": "TODO other keys",
            }
            for line_src, line_tgt in zip(item_lines_src, item_lines_tgt)
        ]
    tasks.append(task)

print("\n".join([
    f"Task {task_i:>3}: "
    f"{len(set([x['documentID'] for x in task])):>4} docs, "
    f"{len(task):>6} lines, "
    f"{sum([len(x['sourceText'].split()) for x in task]):>6} words"
    for task_i, task in enumerate(tasks)
]))

json.dump(tasks, open(f"data/wmt24_general/batches_wave{args.wave}.{args.langs}.json", "w"))