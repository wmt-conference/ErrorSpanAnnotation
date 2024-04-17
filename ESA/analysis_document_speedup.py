from annotations import AppraiseAnnotations
import collections
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

SCHEME = "GEMBA"
anno_esa = AppraiseAnnotations.get_full(SCHEME)

data_times = collections.defaultdict(list)


annot_times = []
for login in anno_esa.login.unique():
    df = anno_esa[anno_esa['login'] == login]
    df = df.sort_values("start_time").reset_index(drop=True)
    for i in range(0, len(df) - 1):
        annot_times.append(df.iloc[i + 1]["start_time"] - df.iloc[i]["start_time"])
df = pd.DataFrame(annot_times).sort_values(by=0)
quantile = df.quantile(0.95)[0]
median = df.median()[0]

df = anno_esa.sort_values("start_time")
times_users = []
for login in anno_esa.login.unique():
    subdf = df[df['login'] == login]
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
for times_user in times_users:
    times_user = smooth(times_user, 40)
    for i, v in enumerate(times_user):
        times_users_big[i].append(v)
    plt.plot(
        times_user,
        color="black", alpha=0.4,
    )

times_users_big = [np.average(v) for v in times_users_big if v]
plt.plot(
    times_users_big,
    color="black", linewidth=4,
)

plt.title(SCHEME)
plt.ylabel("Segment time")
plt.xlabel("Segment progression")
plt.show()