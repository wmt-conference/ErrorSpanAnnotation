import itertools
from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["ESAAI-1", "LLM"], only_overlap=False).dropna()
import collections
import ESA.figutils
import matplotlib.pyplot as plt
import numpy as np
ESA.figutils.matplotlib_default()


def rank_accuracy(method1_v, method2_v):
    systems_mismatch = set()
    hits = []
    for sys1, sys2 in itertools.product(method1_v.keys(), repeat=2):
        hits.append((method1_v[sys1] > method1_v[sys2]) == (method2_v[sys1] > method2_v[sys2]))
        if not (method1_v[sys1] > method1_v[sys2]) == (method2_v[sys1] > method2_v[sys2]):
            systems_mismatch.add(sys1)
            systems_mismatch.add(sys2)
    return np.average(hits), (len(hits)-sum(hits))//2, systems_mismatch


all_sets = []
system_scores = collections.defaultdict(lambda: collections.defaultdict(list))
scores_for_no_gemba_errors = []
scores_for_no_esaai_errors = []

# load different scorings
substitute_100_count = 0
for _, row in df.iterrows():
    system_scores["esaai"][row.systemID].append(row["ESAAI-1_score"])
    if len(row["LLM_error_spans"]) == 0:
        substitute_100_count += 1
        system_scores["substitute_100"][row.systemID].append(100)
        scores_for_no_gemba_errors.append(row["ESAAI-1_score"])
    else:
        system_scores["substitute_100"][row.systemID].append(row["ESAAI-1_score"])
    if len(row["ESAAI-1_error_spans"]) == 0:
        scores_for_no_esaai_errors.append(row["ESAAI-1_score"])
for _, group in df.groupby("sourceID"):
    num_of_no_errors = sum([len(x) == 0 for x in group["LLM_error_spans"]])
    if num_of_no_errors >= 5:
        # ignore "easy" examples
        continue
    for _, row in group.iterrows():
        system_scores["filter_easy"][row.systemID].append(row["ESAAI-1_score"]) 

print(
    "Counts in methods:",
    {method: len(list(method_v.values())[0]) for method, method_v in system_scores.items()}
)
print("Substitute 100 approx count:", 207-substitute_100_count//len(system_scores["esaai"]))

system_scores = {
     method: {sys:np.average(sys_v) for sys, sys_v in method_v.items()}
     for method, method_v in system_scores.items()
}

acc, mismatch_count_sub, systems_mismatch_sub = rank_accuracy(system_scores["esaai"], system_scores["substitute_100"])
print(f"Substitute 100 accuracy: {acc:.1%}")
acc, mismatch_count_easy, systems_mismatch_filter = rank_accuracy(system_scores["esaai"], system_scores["filter_easy"])
print(f"Filter easy accuracy: {acc:.1%}")

systems = list(system_scores["esaai"].keys())
system_scores_base = [system_scores["esaai"][sys] for sys in systems]
system_scores_sub = [system_scores["substitute_100"][sys] for sys in systems]
system_scores_filter = [system_scores["filter_easy"][sys] for sys in systems]
system_colors_sub = ["black" if sys not in systems_mismatch_sub else ESA.figutils.COLORS[0] for sys in systems]
system_colors_filter = ["black" if sys not in systems_mismatch_filter else ESA.figutils.COLORS[0] for sys in systems]

print(f"average score when 0 gemba errors: {np.average(scores_for_no_gemba_errors):.1f}")
print(f"average score when 0 esaai errors: {np.average(scores_for_no_esaai_errors):.1f}")

plt.figure(figsize=(2, 1.3))
plt.scatter(
    system_scores_sub,
    system_scores_base,
    color=system_colors_sub,
    s=40,
    linewidth=0,
)
plt.text(79, 58, f"{mismatch_count_sub} pair\nmismatched", ha="center", fontsize=9, color=ESA.figutils.COLORS[0])
plt.gca().spines[['top', 'right']].set_visible(False)
plt.xlabel("Sys. scores w/ substitution" + " " * 5, size=9)
plt.ylabel("Original sys. score" + " " * 7, size=9)
plt.tight_layout(pad=0.1)
plt.savefig("PAPER_ESAAI/generated_plots/filtering_with_gemba_sub.pdf")
plt.show()

plt.figure(figsize=(2, 1.3))
plt.scatter(
    system_scores_filter,
    system_scores_base,
    color=system_colors_filter,
    s=40,
    linewidth=0,
)
plt.text(75, 58, f"{mismatch_count_easy} pair\nmismatched", ha="center", fontsize=9, color=ESA.figutils.COLORS[0])
plt.gca().spines[['top', 'right']].set_visible(False)
plt.xlabel("Sys. scores w/ filtering", size=9)
plt.ylabel("Original sys. score" + " " * 7, size=9)
plt.tight_layout(pad=0.1)
plt.savefig("PAPER_ESAAI/generated_plots/filtering_with_gemba_easy.pdf")
plt.show()