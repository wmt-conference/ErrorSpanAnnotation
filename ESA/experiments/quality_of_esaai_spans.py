from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view()
import numpy as np

all_sets = []

def get_spans(spans):
    return {(x["start_i"], x["end_i"]) for x in spans if x["start_i"] != "missing"}

def get_spans_wmt(spans):
    return {(x["start"], x["end"]) for x in spans}

for _, row in df.iterrows():
    spans_gemba = get_spans(row["LLM_error_spans"])
    spans_esaai = get_spans(row["ESAAI-1_error_spans"])
    spans_esa = get_spans(row["ESA-1_error_spans"])
    spans_mqm = get_spans(row["MQM-1_error_spans"])
    spans_wmt = get_spans_wmt(row["WMT-MQM_error_spans"])

    all_sets.append({
          "gemba": spans_gemba,
          "esaai": spans_esaai,
          "esaai_kept": spans_gemba & spans_esaai,
          "esaai_removed": spans_gemba - spans_esaai,
          "esaai_added": spans_esaai - spans_gemba,
          "esa": spans_esa,
          "mqm": spans_mqm,
          "wmt": spans_wmt,
    })

all_sets = [x for x in all_sets if x["wmt"] is not None]

def spans_overlap(a, b):
    return b[0] <= a[1] and a[0] <= b[1]

def span_set_similarity(spans_a, spans_b):
    if len(spans_b) == 0:
         return 1
    else:
        return sum([any([spans_overlap(a, b) for a in spans_a]) for b in spans_b])/len(spans_b)

LATEX=False

# for key1, key2 in itertools.product(all_sets[0].keys(), repeat=2):
for key1 in all_sets[0].keys():
    for key2 in ["esa", "mqm", "wmt"]:
    # for key2 in all_sets[0].keys():
        # we are not interested in subsets of that
        if key2.startswith("esaai_"):
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