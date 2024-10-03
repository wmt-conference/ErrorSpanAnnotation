from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["MQM-1", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=False).dropna()
import collections
import matplotlib.pyplot as plt
import numpy as np
import argparse
import ESA.utils
import matplotlib.patches as patches

args = argparse.ArgumentParser()
args.add_argument("scheme", default="ESA", choices=["ESA", "ESAAI", "MQM"])
args = args.parse_args()

plt.figure(figsize=(4, 1.5))

data_times = collections.defaultdict(list)


annot_times = []
def load_times(protocol):
    times_users = []
    for _, local in df.groupby(f"{protocol}_AnnotatorID"):
        times = []
        local.sort_values(by=f"{protocol}_start_time", inplace=True)
        time_median = np.median(local[f"{protocol}_duration_seconds"])
        for _, row in local.iterrows():
            if row[f"{protocol}_duration_seconds"] > 60*5:
                times.append(time_median)
            else:
                times.append(row[f"{protocol}_duration_seconds"])

        times_users.append(times)
    return times_users

if args.scheme == "MQM":
    times_users = load_times(f"{args.scheme}-1")
else:
    times_users = load_times(f"{args.scheme}-1") + load_times(f"{args.scheme}-2")


def smooth(y, box_pts):
    box = np.ones(box_pts) / box_pts
    y_smooth = np.convolve(y, box, mode='valid')
    return y_smooth


times_users_big = [[] for _ in range(len(times_users[0])*2)]
times_users_var = []
for times_user in times_users:
    # compute variation on the first 100 segments
    times_user_average = np.average(times_user[:100])
    times_users_var.append(np.average([abs(x-times_user_average) for x in times_user[:100]]))

    times_user = smooth(times_user, 15)
    for i, v in enumerate(times_user):
        # reindex to 0 .. 100
        i = int(i*100/len(times_user))
        times_users_big[i].append(v)

    plt.plot(
        np.linspace(0, 100, len(times_user)),
        times_user,
        color="black", alpha=0.15,
    )


plt.gca().add_patch(patches.Rectangle(
    (0, 10), 15, 200,
    linewidth=0, edgecolor=None,
    facecolor='#8d8a')
)
plt.text(
    7.5, 105,
    s="learn",
    color="#050",
    ha="center",
    fontsize=9,
    fontweight="black",
)
times_users_big = [np.average(v) for v in times_users_big if v]

slope = (np.average(times_users_big[-10:-5])-np.average(times_users_big[5:10]))/100
print(f"Learned slope: {slope:.4f}s")
slope_init = (times_users_big[15]-times_users_big[1])/15
print(f"Learned slope (first 15%): {slope_init:.4f}s")

plt.plot(
    times_users_big,
    color="black", linewidth=4,
)

plt.ylim(10, 120)

plt.title(f"{args.scheme.replace('ESAAI', ESA.utils.PROTOCOL_DEFINITIONS['ESAAI']['name'])}  ({slope_init:.2f}s per segment)")
plt.ylabel("Segment time (s)", labelpad=-2)
plt.xticks(
    [0, 20, 80, 100],
    ["0%", "20%", "80%", "100%"],
)
plt.xlabel("Annotation progress", labelpad=-8)
plt.yticks([20, 50, 80, 110])

ax = plt.gca()
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout(pad=0.1)
plt.savefig(f"PAPER_ESAAI/generated_plots/document_speedup_{args.scheme}.pdf")
plt.show()