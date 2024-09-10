import json
import glob
import os
import collections
import random
import numpy as np
import itertools
import csv
import matplotlib.pyplot as plt

LANG_2_TO_3 = {
    "en": "eng",
    "de": "deu",
    "cs": "ces",
    "hr": "hrv",
    "pl": "plk",
    "ru": "rus",
    "zh": "zho",
    "uk": "ukr",
    "is": "isl",
    "hi": "hin",
    "ja": "jpn",
    "es": "spa",
}
LANGS = [
    "cs-uk", "en-cs", "en-de", "en-es", "en-hi", "en-is", "en-ja", "en-ru", "en-uk", "en-zh", "ja-zh"
]
LANG_2_TO_NATURAL = {
    "en": "English",
    "de": "German",
    "cs": "Czech",
    "hr": "Croatian",
    "pl": "Polish",
    "ru": "Russian",
    "zh": "Chinese",
    "uk": "Ukrainian",
    "is": "Icelandic",
    "hi": "Hindi",
    "ja": "Japanese",
    "es": "Spanish",
}

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

data_all_tgt = [line for line in data_all if line["type"] == "TGT"]
doc_times = collections.defaultdict(list)
doc_lengths = collections.defaultdict(int)

for line in data_all_tgt:
    key = (line["doc"], line["system"], (line["lang1"], line["lang2"]), str(line["wave"]), line["uid"])
    doc_lengths[key] += 1

for line in data_all_tgt:
    key = (line["doc"], line["system"], (line["lang1"], line["lang2"]), str(line["wave"]), line["uid"])
    doc_times[key].append(float(line["time_start"]))
    doc_times[key].append(float(line["time_end"]))
doc_times = {
    k: max(v)-min(v)
    for k, v in doc_times.items()
}
# normalize to be per segment
doc_times = {
    k: v/doc_lengths[k] for k, v in doc_times.items()
}
doc_times = {
    k: v for k, v in doc_times.items() if v < 60*3
}

print("TOTAL ANNOTATIONS", len(data_all))

def get_filtered_data_for_langs(langs):
    global data_all
    lang1, lang2 = langs.split("-")
    lang1 = LANG_2_TO_3[lang1]
    lang2 = LANG_2_TO_3[lang2]
    return [
        line for line in data_all
        if line["lang1"] == lang1 and line["lang2"] == lang2
    ]

for langs in LANGS:
    lang1, lang2 = langs.split("-")
    lang1_3 = LANG_2_TO_3[lang1]
    lang2_3 = LANG_2_TO_3[lang2]
    lang1 = LANG_2_TO_NATURAL[lang1]
    lang2 = LANG_2_TO_NATURAL[lang2]

    data_langs = get_filtered_data_for_langs(langs)
    data_langs_tgt = [line for line in data_langs if line["type"] == "TGT"]
    unique_itemid_sys = len({line["itemID"] + line["system"] for line in data_langs_tgt})
    unique_itemid_sys_user = len({line["itemID"] + line["system"]+line["uid"] for line in data_langs_tgt})

    doc_times_lang = [
        v for k, v in doc_times.items() if k[2] == (lang1_3, lang2_3)
    ]

    if langs not in {"en-de", "ja-zh"}:
        print(
            r"\tto{" + lang1 + r"}{" + lang2 + r"}",
            f'{np.average([len([x for x in line["esa"] if x["severity"] == "minor"]) for line in data_langs_tgt]):.1f}',
            f'{np.average([len([x for x in line["esa"] if x["severity"] == "major"]) for line in data_langs_tgt]):.1f}',
            f'{np.average([float(line["score"]) for line in data_langs_tgt]):.1f}',
            f'{np.average(doc_times_lang):.1f}s',
            sep=" & ",
            end=r" \\"+"\n"
        )
    else:
        pass


plt.figure(figsize=(4, 2))
times_all = np.array(list(doc_times.values()))
plt.hist(
    times_all,
    weights=np.zeros_like(times_all) + 1. / times_all.size,
    bins=20,
    color="black"
)
plt.xlabel("Annotation time (seconds per segment)")
plt.ylabel("Frequency")
plt.tight_layout(pad=0)
plt.savefig("PAPER_WMT24/generated_plots/time_distribution.pdf")
plt.show()


plt.figure(figsize=(4, 2))
scores_all = np.array([float(line["score"]) for line in data_all])
plt.hist(
    scores_all,
    weights=np.zeros_like(scores_all) + 1. / scores_all.size,
    bins=20,
    color="black"
)
plt.xlabel("Human ESA Score")
plt.ylabel("Frequency")
plt.tight_layout(pad=0)
plt.savefig("PAPER_WMT24/generated_plots/score_distribution.pdf")
plt.show()