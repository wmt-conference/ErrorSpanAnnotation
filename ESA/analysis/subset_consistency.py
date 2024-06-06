raise Exception("This code uses old loader, please refactor.")
import json
import numpy as np
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import collections

df = MergedAnnotations().df

import random

def mqm_like_score(spans):
	return 100-sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

system_scores = collections.defaultdict(lambda: {
	k: {}
	for k in ["esa_score", "gesa_score", "esa_mqm", "gesa_mqm", "gemba_mqm", "mqm_mqm"]
})

for _, row in df.iterrows():
	if type(row["gemba_mqm_span_errors_gemba"]) != list:
		continue
	row["span_errors_esa"] = json.loads(row["span_errors_esa"])
	row["span_errors_mqm"] = json.loads(row["span_errors_mqm"])
	row["span_errors_gemba"] = json.loads(row["span_errors_gemba"])

	system_scores[row.source_seg]["esa_score"][row["system"]]= row["score_esa"]
	system_scores[row.source_seg]["gesa_score"][row["system"]]= row["score_gemba"]
	system_scores[row.source_seg]["esa_mqm"][row["system"]]= mqm_like_score(row["span_errors_esa"])
	system_scores[row.source_seg]["mqm_mqm"][row["system"]]= mqm_like_score(row["span_errors_mqm"])
	system_scores[row.source_seg]["gesa_mqm"][row["system"]]= mqm_like_score(row["span_errors_gemba"])
	system_scores[row.source_seg]["gemba_mqm"][row["system"]]= mqm_like_score(row["gemba_mqm_span_errors_gemba"])


system_scores = list(system_scores.values())
	
def get_sys_ranking(count=206, scoring="esa_score"):
	scores = [x[scoring] for x in random.sample(system_scores, k=min(len(system_scores), count))]
	# transpose
	scores = {sys: [x[sys] for x in scores] for sys in scores[0].keys()}
	# average
	scores = {sys: np.average(sys_v) for sys, sys_v in scores.items()}
	scores = sorted(list(scores.keys()), key=lambda x: scores[x], reverse=True)
	return {sys: i for i, sys in enumerate(scores)}

def rank_acc(rank1, rank2):
	hits = []
	for sys1 in rank1.keys():
		for sys2 in rank1.keys():
			hits.append((rank1[sys1] > rank1[sys2]) == (rank2[sys1] > rank2[sys2]))
		
	return np.average(hits)

import ESA.figutils as figutils
import matplotlib.pyplot as plt

figutils.matplotlib_default()
plt.figure(figsize=(3, 2))

xticks = list(np.arange(10, 210+1, 15))
tick_i = 0
def evaluate_scoring(scoring: str, color="black", linestyle="-"):
	global tick_i
	rank_global = get_sys_ranking(scoring=scoring)
	acc = []
	for count in xticks:
		acc_local = []
		for _ in range(1000):
			rank_local = get_sys_ranking(scoring=scoring, count=count)
			acc_local.append(rank_acc(rank_global, rank_local))
		acc.append(np.average(acc_local))
	
	plt.plot(
		xticks,
		acc,
		label=(
			scoring
				.upper()
				.replace("_", "-")
				.replace("-SCORE", "")
				.replace("-MQM", r"$_\mathrm{MQM}$")
				.replace("GESA", r"ESA$^\mathrm{AI}$")
		),
		color=color,
		linestyle=linestyle,
	)
	plt.text(
		180,
		0.881-tick_i*0.024,
		f"{np.average(acc):.1%}",
		fontsize=8
	)
	tick_i+=1

evaluate_scoring("esa_score", color=figutils.COLORS[0])
evaluate_scoring("esa_mqm", color=figutils.COLORS[0], linestyle="-.")
evaluate_scoring("gesa_score", color=figutils.COLORS[1])
evaluate_scoring("gesa_mqm", color=figutils.COLORS[1], linestyle="-.")
evaluate_scoring("mqm_mqm", linestyle="-.")
evaluate_scoring("gemba_mqm", color=figutils.COLORS[2], linestyle="-.")

plt.legend(handlelength=1.6, labelspacing=0.07, framealpha=0, loc=(0.4, 0))
plt.xticks(list(range(10, 210, 50))+[206])
plt.xlabel("Subset size")

plt.ylim(0.75, None)
plt.yticks(
	[0.8, 1.0],
	["80%", "100%"]
)
plt.ylabel("Rank\naccuracy", labelpad=-24)
plt.gca().spines[['top', 'right']].set_visible(False)

plt.tight_layout(pad=0)
plt.savefig("figures/subset_consistency.pdf")
plt.show()