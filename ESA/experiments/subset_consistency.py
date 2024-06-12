from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "MQM-1"], only_overlap=False).dropna()
import numpy as np
import collections
import random
import argparse

args = argparse.ArgumentParser()
args.add_argument("group", default="1", choices=["1", "2"])
args = args.parse_args()

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
plt.figure(figsize=(2, 1.4))

xticks = list(np.arange(10, 210+1, 15))
DISPLAY_POS = [10, 40, 115, 190]
DISPLAY_POS_i = [i for i, x in enumerate(xticks) if x in DISPLAY_POS]
tick_i = 0
def evaluate_scoring(scoring: str, color="black", linestyle="-"):
	global tick_i
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
		.replace("_MQM", r"$_\mathrm{MQM}$")
		.replace("ESAAI", r"ESA$^\mathrm{AI}$")
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
		label=scoring,
		color=color,
		linestyle=linestyle,
	)
	plt.text(
		170,
		0.87-tick_i*0.035,
		f"{np.average(acc):.1%}",
		fontsize=8
	)
	tick_i+=1

if args.group == "1":
	evaluate_scoring("esaai_score", color=figutils.COLORS[1])
	evaluate_scoring("esaai_mqm", color=figutils.COLORS[1], linestyle="-.")
	evaluate_scoring("gemba_mqm", color=figutils.COLORS[2], linestyle="-.")
elif args.group == "2":
	evaluate_scoring("esa_score", color=figutils.COLORS[0])
	evaluate_scoring("esa_mqm", color=figutils.COLORS[0], linestyle="-.")
	evaluate_scoring("mqm_mqm", linestyle="-.")

plt.legend(
	handlelength=1.5, labelspacing=0.07 if args.group == "1" else 0.3, framealpha=0, loc=(0.15 if args.group == "1" else 0.24, 0),
	markerfirst=False, handletextpad=0.2,
)
# plt.xticks(list(range(10, 210, 50))+[206])
plt.xticks([10, 207])
plt.xlabel("Subset size", labelpad=-5)

plt.ylim(0.79, None)
plt.yticks(
	[0.8, 1.0],
	["80%", "100%"]
)
plt.ylabel("Rank\naccuracy", labelpad=-24)
plt.gca().spines[['top', 'right']].set_visible(False)

plt.tight_layout(pad=0)
plt.savefig(f"PAPER_ESAAI/generated_plots/subset_consistency_{args.group}.pdf")
plt.show()