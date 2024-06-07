from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "MQM-1"], only_overlap=False).dropna()
import numpy as np
import collections
import random

def mqm_like_score(spans):
	return -sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

system_scores = collections.defaultdict(lambda: {
	k: {}
	for k in ["esa_score", "esaai_score", "esa_mqm", "esaai_mqm", "gemba_mqm", "mqm_mqm"]
})

for _, row in df.iterrows():
	system_scores[row.source]["esa_score"][row["systemID"]]= row["ESA-1_score"]
	system_scores[row.source]["esaai_score"][row["systemID"]]= row["ESAAI-1_score"]
	system_scores[row.source]["esa_mqm"][row["systemID"]]= row["ESA-1_score_mqm"]
	system_scores[row.source]["mqm_mqm"][row["systemID"]]= row["MQM-1_score"]
	system_scores[row.source]["esaai_mqm"][row["systemID"]]= row["ESAAI-1_score_mqm"]
	system_scores[row.source]["gemba_mqm"][row["systemID"]]= mqm_like_score(row["LLM_error_spans"])


system_scores = list(system_scores.values())
	
def get_sys_ranking(count=207, scoring="esa_score"):
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
	
	print(scoring)
	plt.plot(
		xticks,
		acc,
		label=(
			scoring
				.upper()
				.replace("_SCORE", "")
				.replace("_MQM", r"$_\mathrm{MQM}$")
				.replace("ESAAI", r"ESA$^\mathrm{AI}$")
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

evaluate_scoring("esaai_mqm", color=figutils.COLORS[1], linestyle="-.")
evaluate_scoring("gemba_mqm", color=figutils.COLORS[2], linestyle="-.")
evaluate_scoring("esaai_score", color=figutils.COLORS[1])
evaluate_scoring("esa_score", color=figutils.COLORS[0])
evaluate_scoring("esa_mqm", color=figutils.COLORS[0], linestyle="-.")
evaluate_scoring("mqm_mqm", linestyle="-.")

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
plt.savefig("PAPER_ESAAI/generated_plots/subset_consistency.pdf")
plt.show()