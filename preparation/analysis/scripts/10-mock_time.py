from analysis.figutils import *


plt.figure(figsize=(4, 1.8))
ax = plt.gca()
ax.spines[["top", "right"]].set_visible(False)

values = [6.2, 5.1, 5.2, 4.7]

plt.bar(
    range(4),
    values,
    color=COLORS_GRAY[0]
)

for v_i, v in enumerate(values):
    plt.text(
        v_i, v-1,
        f"{v:.2f}s",
        ha="center",
        va="center",
        fontsize=12
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
plt.ylabel("Time per segment (s)")

plt.tight_layout(pad=0.1)
plt.savefig("analysis/computed/time_effect_bar.pdf")
plt.show()