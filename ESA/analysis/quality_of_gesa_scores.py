raise Exception("This code uses old loader, please refactor.")

from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view()
import json
import ESA.figutils
import numpy as np
ESA.figutils.matplotlib_default()

all_sets = []

def get_spans(spans):
    return {(x["start_i"], x["end_i"]) for x in spans}

def get_score_mqm(spans):
    return -sum([{"minor": 1, "major": 5, "undecided": 0}[x["severity"]] for x in spans])

for _, row in df.iterrows():
    print(row.keys())
    exit()
    if row.wmt_mqm_span_errors == "None":
         continue

    all_sets.append({
          "gemba_mqm": row["LLM_score"],
          "gesa_mqm": get_score_mqm(row.span_errors_gemba),
          "gesa_score": row.score_gemba,
          "esa_mqm": get_score_mqm(json.loads(row.span_errors_esa)),
          "esa_score": row.score_esa,
          "mqm_mqm": get_score_mqm(json.loads(row.span_errors_mqm)),
          "wmt_mqm": get_score_mqm(row.wmt_mqm_span_errors),
    })

# for key1, key2 in itertools.product(all_sets[0].keys(), repeat=2):
for key1 in all_sets[0].keys():
    for key2 in all_sets[0].keys():
        corr = np.corrcoef([span[key1] for span in all_sets], [span[key2] for span in all_sets])[0,1]
        print(f"{key1:>14}-{key2:<14}: {corr:.0%}")