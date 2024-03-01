from analysis.figutils import *
import numpy as np


plt.figure(figsize=(4, 1.8))
ax1 = plt.gca()
ax2 = ax1.twinx()
ax1.spines["top"].set_visible(False)
ax2.spines["top"].set_visible(False)

values_1 = [0.7, 1.0, 0.6, 0.7]
values_2 = [0.8, 0.6, 0.85, 0.78]

plt.bar(
    np.arange(4)-0.225,
    values_1,
    width=0.45,
    color=COLORS_GRAY[1]
)
plt.bar(
    np.arange(4)+0.225,
    values_2,
    width=0.45,
    color=COLORS_GRAY[2]
)

for v_i, v in enumerate(values_1):
    plt.text(
        v_i-0.225, v-0.1,
        f"{v:.1f}",
        ha="center",
        va="center",
        fontsize=11,
        color="white"
    )
for v_i, v in enumerate(values_2):
    plt.text(
        v_i+0.225, v-0.1,
        f"{v:.0%}".replace("%", "\%"),
        ha="center",
        va="center",
        fontsize=10
    )

plt.xticks(
    range(4),
    [
        "Orig.MQM\nno AI",
        "Simp.MQM\nno AI",
        "Orig.MQM\nAI sug.",
        "Simp.MQM\nAI sug.",
    ]
)
ax1.set_ylabel("Absolute Error ($\downarrow$)")
ax2.set_ylabel(r"Kendall's $\tau$ (\%, $\uparrow$)")

plt.tight_layout(pad=0.1)
plt.savefig("analysis/computed/acc_effect_bar.pdf")
plt.show()