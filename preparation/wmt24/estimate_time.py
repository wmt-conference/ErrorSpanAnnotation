import glob
import json

def get_item_len(item, langs):
    txt = item["targetText"]

    if langs in {"en-ja", "en-zh", "ja-zh"}:
        return len(txt)
    else:
        return len(txt.split())


for f in glob.glob("data/wmt24_general/batches/*.json"):
    if "wave0." not in f:
        continue
    langs = f.split("/")[-1].removeprefix("wave0.").removesuffix(".json")
    data = json.load(open(f, "r"))

    times = [
        sum([get_item_len(item, langs) for item in task["items"]])*0.79
        for task in data
    ]
    times = [
        f"{task/60:>3.0f}m"
        for task in times
    ]
    while times:
        print(langs, " ".join(times[:20]))
        times = times[20:]
    print()