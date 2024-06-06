import pandas as pd
import matplotlib.pyplot as plt


# System (En-De)	DA+SQM	MQM
# Human-refA	87.7	-2.96
# GPT4-5shot	89	-3.72
# ONLINE-W	88.3	-3.95
# ONLINE-B	88.8	-4.71
# ONLINE-Y	88	-5.64
# ONLINE-A	88.1	-5.67
# ONLINE-G	85.5	-6.57
# ONLINE-M	86.7	-6.94
# Lan-BridgeMT	84	-8.67
# LanguageX	82.7	-9.25
# NLLB_Greedy	75.7	-9.54
# NLLB_MBR_BLEU	76.8	-10.79
# AIRC	73.6	-14.23

data_ende = {
    "System (En-De)": ["Human-refA", "GPT4-5shot", "ONLINE-W", "ONLINE-B", "ONLINE-Y", "ONLINE-A", "ONLINE-G", "ONLINE-M", "Lan-BridgeMT", "LanguageX", "NLLB_Greedy", "NLLB_MBR_BLEU", "AIRC"],
    "DA+SQM": [87.7, 89, 88.3, 88.8, 88, 88.1, 85.5, 86.7, 84, 82.7, 75.7, 76.8, 73.6],
    "MQM": [-2.96, -3.72, -3.95, -4.71, -5.64, -5.67, -6.57, -6.94, -8.67, -9.25, -9.54, -10.79, -14.23]
}
data_ende_clusters = {
    "DA+SQM": [74.65, 79.75, 83.35, 84.75, 87.2],
    "MQM": [-12.51, -10.165, -7.504, -6.12, -5.175, -4.33, -3.34]
}

# Zh-En	DA+SQM	MQM
# Lan-BridgeMT	82.9	-2.1
# GPT4-5shot	80.9	-2.31
# Yishu	80.3	-3.23
# ONLINE-B	79.8	-3.39
# HW-TSC	79.1	-3.4
# ONLINE-A	77.8	-3.79
# ONLINE-Y	79.7	-3.79
# ONLINE-G	80	-3.86
# ONLINE-W	80.2	-4.06
# LanguageX	77.2	-4.23
# IOL_Research	77.7	-4.59
# Human-refA	76.1	-4.83
# ONLINE-M	76.9	-5.43
# ANVITA	72.6	-6.08
# NLLB_MBR_BLEU	76.2	-6.36
# NLLB_Greedy	74	-6.57

data_zhen = {
    "System (Zh-En)": ["Lan-BridgeMT", "GPT4-5shot", "Yishu", "ONLINE-B", "HW-TSC", "ONLINE-A", "ONLINE-Y", "ONLINE-G", "ONLINE-W", "LanguageX", "IOL_Research", "Human-refA", "ONLINE-M", "ANVITA", "NLLB_MBR_BLEU", "NLLB_Greedy"],
    "DA+SQM": [82.9, 80.9, 80.3, 79.8, 79.1, 77.8, 79.7, 80, 80.2, 77.2, 77.7, 76.1, 76.9, 72.6, 76.2, 74],
    "MQM": [-2.1, -2.31, -3.23, -3.39, -3.4, -3.79, -3.79, -3.86, -4.06, -4.23, -4.59, -4.83, -5.43, -6.08, -6.36, -6.57]
}

data_zhen_clusters = {
    "DA+SQM": [77.05, 80.6],
    "MQM": [-5.755, -5.13, -4.41, -3.595, -3.31, -2.76, -2.205]
}


# generate scatter plot for each set of languages, make each plot exactly square
fig, ax = plt.subplots(1, 2, figsize=(9, 3))

df_zhen = pd.DataFrame(data_zhen)
df_ende = pd.DataFrame(data_ende)
df_ende.plot.scatter(x="DA+SQM", y="MQM", ax=ax[1], color="black")
df_zhen.plot.scatter(x="DA+SQM", y="MQM", ax=ax[0], color="black")
# ax[0].set_xlim(73, 89)
# ax[1].set_xlim(73, 89)
# show x-axis only with whole numbers, do not jump by 0.5
ax[1].xaxis.set_major_locator(plt.MaxNLocator(integer=True))
ax[0].xaxis.set_major_locator(plt.MaxNLocator(integer=True))
# put title with language pair on top of each plot
ax[1].set_title("English-German (paragraph-level)")
ax[0].set_title("Chinese-English (sentence-level)")
# to plot ende add vertical lines for clusters of DA+SQM, and horizontal for MQM
for cluster in data_ende_clusters["DA+SQM"]:
    ax[1].axvline(cluster, color="#bc272d", linestyle="--")
for cluster in data_ende_clusters["MQM"]:
    ax[1].axhline(cluster, color="#0000a2", linestyle="--")
# to plot zhen add vertical lines for clusters of DA+SQM, and horizontal for MQM
for cluster in data_zhen_clusters["DA+SQM"]:
    ax[0].axvline(cluster, color="#bc272d", linestyle="--")
for cluster in data_zhen_clusters["MQM"]:
    ax[0].axhline(cluster, color="#0000a2", linestyle="--")
# save the plot into "generated_plots/wmt23_mqm_vs_dasqm.pdf" folder into pdf format
plt.tight_layout()
plt.savefig("generated_plots/wmt23_mqm_vs_dasqm.pdf")