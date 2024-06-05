from ESA.annotations import AppraiseAnnotations
import collections
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

args = argparse.ArgumentParser()
args.add_argument("scheme", default="ESA")
args = args.parse_args()

plt.figure(figsize=(4, 1.5))

anno_esa = AppraiseAnnotations.get_full(args.scheme)
data_times = collections.defaultdict(list)


annot_times = []
for AnnotatorID in anno_esa.AnnotatorID.unique():
    df = anno_esa[anno_esa['AnnotatorID'] == AnnotatorID]
    df = df.sort_values("start_time").reset_index(drop=True)
    for i in range(0, len(df) - 1):
        annot_times.append(df.iloc[i + 1]["start_time"] - df.iloc[i]["start_time"])
df = pd.DataFrame(annot_times).sort_values(by=0)
quantile = df.quantile(0.95)[0]
median = df.median()[0]

df = anno_esa.sort_values("start_time")
times_users = []
for AnnotatorID in anno_esa.AnnotatorID.unique():
    subdf = df[df['AnnotatorID'] == AnnotatorID]
    reducing_time = 0
    previous_timestamp = subdf.iloc[0]["start_time"]
    times_user = []
    for i in range(1, len(subdf)):
        index = subdf.index[i]

        diff = df.loc[index]["start_time"] - previous_timestamp
        if diff > quantile:
            reducing_time += diff - median

        if diff > quantile:
            # use the previous value instead of median
            if times_user:
                times_user.append(times_user[-1])
        else:
            times_user.append(diff)
        previous_timestamp = df.loc[index]["start_time"]
    times_users.append(times_user)


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
        color="black", alpha=0.3,
    )

times_users_big = [np.average(v) for v in times_users_big if v]

slope = (np.average(times_users_big[-10:-5])-np.average(times_users_big[5:10]))/100
print(f"Learned slope: {slope:.4f}s")
slope_init = (times_users_big[15]-times_users_big[1])/15
print(f"Learned slope (first 15%): {slope_init:.4f}s")
print(f"ABS variation: {np.average(times_users_var):.4f}s")

plt.plot(
    times_users_big,
    color="black", linewidth=4,
)

plt.ylim(10, 120)

plt.title(f"{args.scheme.replace('GEMBA', r'ESA$^\mathrm{AI}$')}  ({slope:.2f}s per segment)")
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
plt.savefig(f"figures/document_speedup_{args.scheme}.pdf")
plt.show()