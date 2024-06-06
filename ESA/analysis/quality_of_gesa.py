raise Exception("This code uses old loader, please refactor.")
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import json
import ESA.figutils
import numpy as np
ESA.figutils.matplotlib_default()

df = MergedAnnotations().df

all_sets = []

def get_spans(spans):
    return {(x["start_i"], x["end_i"]) for x in spans}

def get_spans_wmt(spans):
    if spans == "None":
        return None
    return {(x["start"], x["end"]) for x in spans}

for _, row in df.iterrows():
    if type(row.gemba_mqm_span_errors_gemba) != list:
            continue
    spans_gemba = get_spans(row.gemba_mqm_span_errors_gemba)
    spans_gesa = get_spans(json.loads(row.span_errors_gemba))
    spans_esa = get_spans(json.loads(row.span_errors_esa))
    spans_mqm = get_spans(json.loads(row.span_errors_mqm))
    spans_wmt = get_spans_wmt(row.wmt_mqm_span_errors)

    all_sets.append({
          "gemba": spans_gemba,
          "gesa": spans_gesa,
          "gesa_kept": spans_gemba & spans_gesa,
          "gesa_removed": spans_gemba - spans_gesa,
          "gesa_added": spans_gesa - spans_gemba,
          "esa": spans_esa,
          "mqm": spans_mqm,
          "wmt": spans_wmt,
    })

all_sets = [x for x in all_sets if x["wmt"] is not None]

def span_set_similarity(spans_a, spans_b):
    if len(spans_b) == 0:
         return 1
    else:
        return len(spans_a & spans_b)/len(spans_b)

LATEX=False

# for key1, key2 in itertools.product(all_sets[0].keys(), repeat=2):
for key1 in all_sets[0].keys():
    for key2 in ["esa", "mqm", "wmt"]:
    # for key2 in all_sets[0].keys():
        # we are not interested in subsets of that
        if key2.startswith("gesa_"):
            continue
        
        sim = np.average([
            span_set_similarity(span[key1], span[key2])
            for span in all_sets
        ])

        if LATEX:
            print(f"& {sim:.0%}".replace("%", "\\%"), end=" ")
        else:
            print(f"{key1:>14}-{key2:<14}: {sim:.0%}")

    if LATEX:
        print("\\\\")