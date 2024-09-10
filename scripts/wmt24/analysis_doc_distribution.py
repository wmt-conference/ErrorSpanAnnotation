import json
import glob
import os
import collections
import random
import numpy as np
import itertools
import csv

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
        fieldnames=["uid", "system", "itemID", "type", "lang1", "lang2", "score", "doc", "unk", "esa"]
    ))
]
data_all = [
    line for line in data_all
    if "tutorial" not in line["doc"]
]
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

OUTPUT_TO_AVG = collections.defaultdict(list)

for langs in LANGS:
    SEC_TUTORIAL = json.load(open(f"data/tutorial/de-en.esa.json", "r"))
    SYSTEMS = json.load(open(f"data/wmt24_general/systems.json", "r"))[langs]
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


    lines_src = load_tsv(f"data/wmt24_general/sources/{langs}.txt")
    lines_doc = load_tsv(
        f"data/wmt24_general/documents/{langs}.docs",
        tsv_index=1
    )
    lines_domain = load_tsv(
        f"data/wmt24_general/documents/{langs}.docs",
        tsv_index=0
    )

    # trim documents to first 10
    OUTPUT_DOCUMENT_CLIPPED = {}
    doc_counter = collections.Counter()
    for line_i, line in enumerate(lines_doc):
        OUTPUT_DOCUMENT_CLIPPED[line] = False
        if doc_counter[line] >= 10:
            lines_doc[line_i] = None
            OUTPUT_DOCUMENT_CLIPPED[line] = True
            
        doc_counter[line] += 1


    OUTPUT_TO_AVG["line count old"].append(len(lines_src))
    OUTPUT_TO_AVG["line count new"].append(len([x for x in lines_doc if x is not None]))
    OUTPUT_TO_AVG["doc count"].append(len(doc_counter))
    OUTPUT_TO_AVG["docs of size 1"].append(len([x for x in doc_counter.values() if x == 1]))
    OUTPUT_TO_AVG["docs speech"].append(len([k for k, v in doc_counter.items() if "speech" in k and v == 1]))
    OUTPUT_TO_AVG["docs of size >10"].append(len([x for x in doc_counter.values() if x > 10]))
    OUTPUT_TO_AVG["docs clipped"].append(np.average(list(OUTPUT_DOCUMENT_CLIPPED.values())))

    lang1, lang2 = langs.split("-")
    lang1 = LANG_2_TO_NATURAL[lang1]
    lang2 = LANG_2_TO_NATURAL[lang2]

    data_langs = get_filtered_data_for_langs(langs)
    data_langs_tgt = [line for line in data_langs if line["type"] == "TGT"]
    unique_itemid_sys = len({line["itemID"] + line["system"] for line in data_langs_tgt})
    unique_itemid_sys_user = len({line["itemID"] + line["system"]+line["uid"] for line in data_langs_tgt})

    if langs not in {"en-de", "ja-zh"}:
        print(
            r"\tto{" + lang1 + r"}{" + lang2 + r"}",
            len([x for x in lines_doc if x is not None]),
            len(doc_counter),
            len(SYSTEMS),
            f"{unique_itemid_sys_user/unique_itemid_sys:.1f}",
            "TODO",
            len({x["uid"] for x in data_langs}),
            len(data_langs) // len(SYSTEMS),
            sep=" & ",
            end=r" \\"+"\n"
        )
    else:
        pass

for k, v in OUTPUT_TO_AVG.items():
    print(f"{k:>20}", f"{np.average(v):.2f}", f"({np.min(v):.2f}, {np.max(v):.2f})",)