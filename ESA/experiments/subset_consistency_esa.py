from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESA-2", "MQM-1", "WMT-MQM", "WMT-DASQM"], only_overlap=False).dropna()
import numpy as np
import collections
import random

def mqm_like_score(spans):
	return -sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

system_scores = collections.defaultdict(lambda: {
	k: {}
	for k in ["esa_score", "da_score", "esa_mqm", "mqm_mqm", "mqmwmt_mqm"]
})

for _, row in df.iterrows():
	system_scores[row.source]["esa_score"][row["systemID"]]= row["ESA-1_score"]
	system_scores[row.source]["da_score"][row["systemID"]]= row["WMT-DASQM_score"]
	system_scores[row.source]["esa_mqm"][row["systemID"]]= row["ESA-1_score_mqm"]
	system_scores[row.source]["mqm_mqm"][row["systemID"]]= row["MQM-1_score"]
	system_scores[row.source]["mqmwmt_mqm"][row["systemID"]]= row["WMT-MQM_score"]


system_scores = list(system_scores.values())
	
def get_sys_ranking(count=207, scoring="esa_score", seed=0):
	random.seed(seed)
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
plt.figure(figsize=(4, 3))

xticks = list(np.arange(10, 160+1, 15))
DISPLAY_POS = [10, 40, 115, 190]
DISPLAY_POS_i = [i for i, x in enumerate(xticks) if x in DISPLAY_POS]
def evaluate_scoring(scoring: str, color="black", linestyle="-", linewidth=2):
	rank_global = get_sys_ranking(scoring=scoring, seed=0)
	acc = []
	for count in xticks:
		acc_local = []
		for seed in range(1000):
			rank_local = get_sys_ranking(scoring=scoring, count=count, seed=seed)
			acc_local.append(rank_acc(rank_global, rank_local))
		acc.append(np.average(acc_local))
	
	scoring = (scoring
		.upper()
		.replace("_SCORE", "")
		.replace("_MQM", r"$_\mathrm{spans}$")
		.replace("WMT", r"$^\mathrm{WMT}$")
		.replace("DA", r"DA+SQM")
	)
	print(
		scoring,
		*[f"{acc[i]:.2%}".replace("%", r"\%") for i in DISPLAY_POS_i],
		sep=" & ",
		end=" \\\\\n",
	)
	plt.plot(
		xticks,
		acc,
		label=scoring + f" ({np.average(acc):.1%})",
		color=color,
		linestyle=linestyle,
		linewidth=linewidth,
	)

evaluate_scoring("mqmwmt_mqm", color=figutils.COLORS[0])
evaluate_scoring("da_score", color=figutils.COLORS[1])
evaluate_scoring("esa_score", color=figutils.COLORS[2])
evaluate_scoring("esa_mqm", color=figutils.COLORS[2], linestyle=":")
evaluate_scoring("mqm_mqm", color=figutils.COLORS[3])

plt.annotate(
	text="compare",
	xy=(0.75, 0.31),
	xytext=(0.84, 0.3),
	xycoords="figure fraction",
	textcoords="figure fraction",
	arrowprops=dict(arrowstyle="->"),
)
plt.annotate(
	text="",
	xy=(0.75, 0.2),
	xytext=(0.84, 0.3),
	xycoords="figure fraction",
	textcoords="figure fraction",
	arrowprops=dict(arrowstyle="->"),
)

plt.legend(
	handlelength=4,
	labelspacing=0.3,
	framealpha=0,
	loc=(0.2, 0.02),
	markerfirst=False,
	handletextpad=0.2,
)
plt.xticks(list(range(10, 160, 50))+[160])
plt.xlabel("Subset size")

plt.ylim(0.75, 1.02)
plt.yticks(
	[0.75, 0.8, 0.95, 1.0],
	["75%", "80%", "95%", "100%"]
)
plt.ylabel("System rank\naccuracy", labelpad=-24)
plt.gca().spines[['top', 'right']].set_visible(False)

plt.tight_layout(pad=0)
plt.savefig(f"PAPER_ESA/generated_plots/subset_consistency.pdf")
plt.show()