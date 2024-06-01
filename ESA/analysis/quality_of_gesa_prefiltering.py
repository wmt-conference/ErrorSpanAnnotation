import itertools
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import collections
import json
import ESA.figutils
import numpy as np
ESA.figutils.matplotlib_default()

df = MergedAnnotations().df

all_sets = []

def get_spans(spans):
    return {(x["start_i"], x["end_i"]) for x in spans}

def get_score_mqm(spans):
    if spans == "None":
        return None
    return -sum([{"minor": 1, "major": 5, "undecided": 0}[x["severity"]] for x in spans])

system_scores = collections.defaultdict(lambda: collections.defaultdict(list))

for _, row in df.iterrows():
    if type(row.gemba_mqm_span_errors_gemba) != list:
            continue
    
    system_scores["gesa"][row.system].append(row.score_gemba)
    if len(row.gemba_mqm_span_errors_gemba) == 0:
        system_scores["gesa_filter"][row.system].append(100) 
    else:
        system_scores["gesa_filter"][row.system].append(row.score_gemba)

system_scores = {
     method: {sys:np.average(sys_v) for sys, sys_v in method_v.items()}
     for method, method_v in system_scores.items()
}
def rank_accuracy(method1_v, method2_v):
    hits = []
    for sys1, sys2 in itertools.product(method1_v.keys(), repeat=2):
        hits.append((method1_v[sys1] > method1_v[sys2]) == (method2_v[sys1] > method2_v[sys2]))
    return np.average(hits)

for method1, method2 in itertools.combinations(system_scores.keys(), 2):
    acc = rank_accuracy(system_scores[method1], system_scores[method2])
    print(f"{method1:>14}-{method2:<14}: {acc:.0%}")