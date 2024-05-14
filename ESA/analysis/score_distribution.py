import json
import numpy as np
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import collections

df = MergedAnnotations().df


statistics_collector = {
	schema: collections.defaultdict(list)
	for schema in ["esa", "gesa", "gemba", "mqm"]
}

def mqm_like_score(spans):
	return 100-sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

for _, row in df.iterrows():
	if type(row["gemba_mqm_span_errors_gemba"]) != list:
		continue
	span_errors_esa = json.loads(row["span_errors_esa"])
	span_errors_mqm = json.loads(row["span_errors_mqm"])

	statistics_collector["esa"]["score"].append(row["score_esa"])
	statistics_collector["esa"]["score_mqm"].append(mqm_like_score(span_errors_esa))
	statistics_collector["mqm"]["score"].append(100+row["score_mqm"])

# plotting part
import matplotlib.pyplot as plt
import ESA.figutils as figutils

figutils.matplotlib_default()


fig, ax = plt.subplots(3, 1, figsize=(4, 2.8))

def half_violin(v1, color, alpha=0.7):
	for pc in v1['bodies']:
		pc.set_facecolor(color)		
		pc.set_alpha(alpha)
		pc.set_aa(True)
		# get the center
		m = np.mean(pc.get_paths()[0].vertices[:, 1])
		# modify the paths to not go further left than the center
		pc.get_paths()[0].vertices[:, 1] = np.clip(
			pc.get_paths()[0].vertices[:, 1],
			m, np.inf
		)

half_violin(ax[0].violinplot(
	statistics_collector["esa"]["score"],
	vert=False,
	showextrema=False,
), color=figutils.COLORS[0])
ax[0].set_ylabel("ESA", rotation=0)
ax[0].yaxis.set_label_coords(0.096, 0.3)

half_violin(ax[1].violinplot(
	statistics_collector["esa"]["score_mqm"],
	vert=False,
	showextrema=False,
), color=figutils.COLORS[0], alpha=0.4)
ax[1].set_ylabel("ESA MQM-like", rotation=0)
ax[1].yaxis.set_label_coords(0.188, 0.3)

half_violin(ax[2].violinplot(
	statistics_collector["mqm"]["score"],
	vert=False,
	showextrema=False,
), color=figutils.COLORS[1])
ax[2].set_ylabel("MQM", rotation=0)
ax[2].yaxis.set_label_coords(0.1, 0.3)


ax[2].set_xlabel("Score")
for ax_i, ax in enumerate(ax):
	ax.set_yticks([])
	if ax_i != 0:
		ax.set_xlim(90, 100)
	else:
		ax.set_xlim(0, 100)
	ax.set_ylim(1, None)
	ax.spines[['top', 'right', 'left']].set_visible(False)


plt.tight_layout(pad=0)
plt.savefig("figures/score_distribution.pdf")
plt.show()