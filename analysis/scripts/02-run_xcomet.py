import collections
import glob
import json
from comet import download_model, load_from_checkpoint
import torch
import argparse
import os

args = argparse.ArgumentParser()
args.add_argument("--year", default="wmt23")
args.add_argument("--langs", default="en-de")
args.add_argument("--comet", default="XL")
args.add_argument("--bf16", action="store_true")
args.add_argument("--segments-from-batch", default=None)
args = args.parse_args()


def find_file(filename):
    if os.path.exists("data/mt-metrics-eval-v2-custom/" + filename):
        return "data/mt-metrics-eval-v2-custom/" + filename
    if os.path.exists("data/mt-metrics-eval-v2/" + filename):
        return "data/mt-metrics-eval-v2/" + filename
    raise Exception("File " + filename + " not found")


if args.segments_from_batch is not None:
    allowed_items = {
        obj["_item"]
        for task in json.load(open(args.segments_from_batch, "r"))
        for obj in task["items"]
        if "_item" in obj
    }
else:
    allowed_items = None

sources = [
    x.strip() for x in open(find_file(f"{args.year}/sources/{args.langs}.txt"), "r")
]
# we need references for COMET
references = [
    x.strip()
    for x in open(find_file(f"{args.year}/references/{args.langs}.refA.txt"), "r")
]
documents = [
    x.strip().split("\t")[1]
    for x in open(find_file(f"{args.year}/documents/{args.langs}.docs"), "r")
]

data_mqm = collections.defaultdict(list)

# use any metrics rating to get _item
_file = glob.glob(
    f"data/mt-metrics-eval-v2/{args.year}/metric-scores/{args.langs}/*.seg.score"
)[0]
for line in open(
    _file,
    "r",
):
    sys, mqm = line.strip().split("\t")
    data_mqm[sys].append({"mqm": []})
systems = list(data_mqm.keys())

data_flat = []
# the ordering of systems should be preserved
for sys in systems:
    print(len(data_mqm[sys]), "of", sys)
    targets = [
        x.strip()
        for x in open(
            find_file(f"{args.year}/system-outputs/{args.langs}/{sys}.txt"),
            "r",
        )
    ]
    for seg_i, (obj, target, source, reference, document) in enumerate(
        zip(data_mqm[sys], targets, sources, references, documents)
    ):
        obj["system"] = sys
        obj["_item"] = f"{sys} | {seg_i}"
        obj["mqm"] = (
            "compute"
            if allowed_items is None or obj["_item"] in allowed_items
            else "None"
        )
        obj["documentID"] = document
        obj["sourceID"] = f"{args.year}"
        obj["targetID"] = f"{args.year}.{sys}"
        obj["sourceText"] = source
        obj["targetText"] = target
        obj["referenceText"] = reference
        data_flat.append(obj)

# make sure that we have as many sources as all systems
assert all([len(v) == len(sources) for v in data_mqm.values()])

to_qe = [obj for obj in data_flat if obj["mqm"] == "compute"]
print(len(to_qe), "to be QE'd")

model_path = download_model("Unbabel/XCOMET-" + args.comet)
print(model_path)
model = load_from_checkpoint(model_path)
if args.bf16:
    model = model.bfloat16()
_comet_data = [
    {
        "src": x["sourceText"],
        "mt": x["targetText"],
        "ref": x["referenceText"],
    }
    for x in to_qe
]
model_output = model.predict(_comet_data, batch_size=1, gpus=torch.cuda.device_count())

for obj, mqm in zip(to_qe, model_output.metadata.error_spans):
    # manually fix xCOMET alignment
    for x in mqm:
        x["start"] = obj["targetText"].index(x["text"]) if x["text"] in obj["targetText"] else x["start"]
        x["end"] = x["start"] + len(x["text"])
    obj["mqm"] = json.dumps(mqm)

with open(
    f"data/mt-metrics-eval-v2-custom/{args.year}/metric-scores/{args.langs}/XCOMET-{args.comet}.seg.rating",
    "w",
) as f:
    f.write("\n".join([
        f"{x['system']}\t{x['mqm']}"
        for x in data_flat
    ]))

"""
# Note: this works but is lousy because the job-name needs to be set to "bash"
sbatch \
    --gpus=2 \
    --mem-per-cpu=6G \
    --ntasks=20 \
    --wrap="python3 ./analysis/scripts/02-run_xcomet.py --segments-from-batch data/batches_wmt23_en-cs.json --langs en-cs --year wmt23 --comet XL -bf16" \
    --output="logs/xcomet-xl.out2" \
    --error="logs/xcomet-xl.err2" \
    --job-name="bash" \
    --time=0-2 \
;

sbatch \
    --gpus=2 \
    --mem-per-cpu=6G \
    --ntasks=20 \
    --wrap="python3 ./analysis/scripts/02-run_xcomet.py --segments-from-batch data/batches_wmt23_en-cs.json --langs en-cs --year wmt23 --comet XXL -bf16" \
    --output="logs/xcomet-xxl.out2" \
    --error="logs/xcomet-xxl.err2" \
    --job-name="bash" \
    --time=0-2 \
;


srun \
    --gpus=2 \
    --mem-per-cpu=6G \
    --ntasks=20 \
    --time=0-4 \
    --pty bash \
;

# Note: unsure if this works
sbatch \
    --gpus=2 \
    --ntasks-per-node=2 \
    --cpus-per-task=10 \
    --mem-per-cpu=3G \
    --wrap="python3 ./analysis/scripts/02-run_xcomet.py --segments-from-batch data/batches_wmt23_en-cs.json --langs en-cs --year wmt23 --comet XL" \
    --output="logs/xcomet-xl.out" \
    --error="logs/xcomet-xl.err" \
    --job-name="comet-xl" \
    --time=0-2 \
;

sbatch \
    --gpus=2 \
    --ntasks-per-node=2 \
    --cpus-per-task=10 \
    --mem-per-cpu=7G \
    --wrap="python3 ./analysis/scripts/02-run_xcomet.py --segments-from-batch data/batches_wmt23_en-cs.json --langs en-cs --year wmt23 --comet XXL" \
    --output="logs/xcomet-xxl.out" \
    --error="logs/xcomet-xxl.err" \
    --job-name="comet-xxl" \
    --time=0-2 \
;
"""
