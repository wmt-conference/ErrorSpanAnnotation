import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import json
import itertools
import ESA.figutils
import numpy as np
ESA.figutils.matplotlib_default()

df = MergedAnnotations().df

all_sets = []

def get_spans(spans):
      return {(x["start_i"], x["end_i"]) for x in spans}

# ['login_mqm', 'system', 'itemID', 'is_bad', 'source_lang', 'target_lang',
#        'score_mqm', 'documentID', 'span_errors_mqm', 'start_time_mqm',
#        'end_time_mqm', 'duration_seconds_mqm', 'AnnotatorID_mqm',
#        'valid_segment', 'source_seg', 'translation_seg', 'login_esa',
#        'score_esa', 'span_errors_esa', 'start_time_esa', 'end_time_esa',
#        'duration_seconds_esa', 'AnnotatorID_esa', 'login_gemba', 'score_gemba',
#        'span_errors_gemba', 'start_time_gemba', 'end_time_gemba',
#        'duration_seconds_gemba', 'AnnotatorID_gemba',
#        'gemba_mqm_span_errors_gemba']

for _, row in df.iterrows():
    if type(row.gemba_mqm_span_errors_gemba) != list:
            continue
    spans_gemba = get_spans(row.gemba_mqm_span_errors_gemba)
    spans_gesa = get_spans(json.loads(row.span_errors_gemba))
    spans_esa = get_spans(json.loads(row.span_errors_esa))
    spans_mqm = get_spans(json.loads(row.span_errors_mqm))

    all_sets.append({
          "gemba": spans_gemba,
          "gesa": spans_gesa,
          "gesa_kept": spans_gemba & spans_gesa,
          "gesa_removed": spans_gemba - spans_gesa,
          "gesa_added": spans_gesa - spans_gemba,
          "esa": spans_esa,
          "mqm": spans_mqm,
    })


def span_set_similarity(spans_a, spans_b):
    if len(spans_b) == 0:
         return 1
    else:
        return len(spans_a & spans_b)/len(spans_b)

LATEX=True

# for key1, key2 in itertools.product(all_sets[0].keys(), repeat=2):
for key1 in all_sets[0].keys():
    for key2 in all_sets[0].keys():
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