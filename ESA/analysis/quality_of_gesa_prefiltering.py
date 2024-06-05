import itertools
import json
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import collections
import ESA.figutils
import matplotlib.pyplot as plt
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
scores_for_no_gemba_errors = []
scores_for_no_gesa_errors = []

for _, row in df.iterrows():
    if type(row.gemba_mqm_span_errors_gemba) != list:
            continue
    
    system_scores["gesa"][row.system].append(row.score_gemba)
    if len(row.gemba_mqm_span_errors_gemba) == 0:
        system_scores["gesa_filter"][row.system].append(100) 
        scores_for_no_gemba_errors.append(row.score_gemba)
    else:
        system_scores["gesa_filter"][row.system].append(row.score_gemba)
    if len(json.loads(row.span_errors_gemba)) == 0:
        scores_for_no_gesa_errors.append(row.score_gemba)

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

systems = list(system_scores["gesa"].keys())
system_scores_base = [system_scores["gesa"][sys] for sys in systems]
system_scores_filter = [system_scores["gesa_filter"][sys] for sys in systems]

print(f"average score when 0 gemba errors: {np.average(scores_for_no_gemba_errors):.1f}")
print(f"average score when 0 esa errors: {np.average(scores_for_no_gesa_errors):.1f}")

plt.figure(figsize=(3, 1.5))
plt.scatter(
    system_scores_base,
    system_scores_filter,
    color="black",
    s=10
)
plt.gca().spines[['top', 'right']].set_visible(False)
plt.yticks([60, 70, 80, 85])
plt.xticks([60, 70, 80, 85])
plt.xlabel("System scores (original)")
plt.ylabel("System scores\n(with filtering)")
plt.tight_layout(pad=0.1)
plt.savefig("figures/quality_gesa_prefiltering.pdf")
plt.show()