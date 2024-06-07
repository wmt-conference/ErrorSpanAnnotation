raise Exception("This code uses old loader, please refactor.")
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import numpy as np
import collections
import matplotlib.pyplot as plt
import ESA.figutils as figutils

figutils.matplotlib_default()

raise Exception("Migration not finished")

anno = MergedAnnotations().df

to_average_users = []
for login in anno.AnnotatorID.unique():
    df = anno[anno["AnnotatorID"] == login]
    v_time = list(df["start_time"])
    v_time.sort()
    v_time = [b-a for a, b in zip(v_time, v_time[1:])]
    v_time_median, v_time_quantile = np.median(v_time), np.quantile(v_time, 0.9)

    prev_time = 0
    to_average = collections.defaultdict(list)
    for _, row in df.iterrows():
        if row["span_errors_gemba"] is None or row["span_errors"] is None:
            continue

        v_time = row["start_time"]-prev_time
        if v_time > v_time_quantile or v_time <= 0:
            v_time = v_time_median
        prev_time = row["start_time"]
        to_average["time"].append(v_time)
        to_average["span_gemba"].append(len(row["span_errors_gemba"]))
        to_average["span_kept"].append(len([
            a for a in row["span_errors_gemba"]
            if [b for b in row["span_errors"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
        ]))
        to_average["span_removed"].append(len([
            a for a in row["span_errors_gemba"]
            if not [b for b in row["span_errors"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
        ]))
        to_average["span_added"].append(len([
            a for a in row["span_errors"]
            if not [b for b in row["span_errors_gemba"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
        ]))

        to_average["span_final"].append(len(row["span_errors"]))

    to_average_users.append({k:np.average(v) for k,v in to_average.items()})

to_average_users.sort(key=lambda x: x["time"])
for user in to_average_users:
    print(
        f"{user['time']:.1f}s",
        f"{user['span_gemba']:.1f}",
        f"{user['span_kept']:.1f}",
        f"{user['span_removed']:.1f}",
        f"{user['span_added']:.1f}",
        f"{user['span_final']:.1f}",
        sep = " & ",
        end=" \\\\\n"
    )

print(r"\midrule")
# hack to average
user = {k:np.average([x[k] for x in to_average_users]) for k in user.keys()}
print(
    f"{user['time']:.1f}s",
    f"{user['span_gemba']:.1f}",
    f"{user['span_kept']:.1f}",
    f"{user['span_removed']:.1f}",
    f"{user['span_added']:.1f}",
    f"{user['span_final']:.1f}",
    sep = " & ",
    end=" \\\\\n"
)

def plot_complex(to_average_users, scheme):
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(2.5, 3), height_ratios=[2, 1])

    if scheme == "GEMBA":
        ax0.bar(
            range(len(to_average_users)),
            height=[user['span_removed']+user['span_kept'] for user in to_average_users],
            color=figutils.COLORS[0],
            label="Removed",
            # default is 0.8 so this makes it be "in the back"
            width=0.79,
        )
        ax0.bar(
            range(len(to_average_users)),
            height=[user['span_kept'] for user in to_average_users],
            color=figutils.COLORS[3],
            label="Kept",
        )
        ax0.bar(
            range(len(to_average_users)),
            height=[-user['span_added'] for user in to_average_users],
            color=figutils.COLORS[1],
            label="Added",
        )
    elif scheme == "ESA":
        ax0.bar(
            range(len(to_average_users)),
            height=[-user['span_final'] for user in to_average_users],
            color=figutils.COLORS[1],
            label="Added",
        )

    ax0.set_yticks([-1, 0, 1], ["+1", "0", "+1"])
    ax0.set_xticks([])
    ax0.set_ylabel("Segments")
    ax0.legend(
        facecolor="#ccc",
        handlelength=0.5,
        ncols=3,
        columnspacing=0.5,
        loc="lower center",
    )
    ax0.set_ylim(-2.2, 1.8)
    ax0.spines[["top", "right"]].set_visible(False)

    ax1.scatter(
        range(len(to_average_users)),
        [user["time"] for user in to_average_users],
        color="black",
    )
    ax1.set_ylabel("Time")
    ax1.set_xlabel(f"User ({scheme.replace('GEMBA', r'ESA$^\mathrm{AI}$')})")
    ax1.set_xticks(range(len(to_average_users)), [""]*len(to_average_users))
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.set_ylim(5, 85)

    plt.tight_layout(pad=0.1)
    plt.savefig(f"generated_plots/edit_degree_{scheme}.pdf")
    plt.show()
        
plot_complex(to_average_users, scheme="GEMBA")

anno = AppraiseAnnotations.get_full("ESA")

to_average_users = []
for login in anno.AnnotatorID.unique():
    df = anno[anno["AnnotatorID"] == login]
    v_time = list(df["start_time"])
    v_time.sort()
    v_time = [b-a for a, b in zip(v_time, v_time[1:])]
    v_time_median, v_time_quantile = np.median(v_time), np.quantile(v_time, 0.9)

    prev_time = 0
    to_average = collections.defaultdict(list)
    for _, row in df.iterrows():
        if type(row["span_errors"]) is float:
            continue

        v_time = row["start_time"]-prev_time
        if v_time > v_time_quantile or v_time <= 0:
            v_time = v_time_median
        prev_time = row["start_time"]
        to_average["time"].append(v_time)
        to_average["span_final"].append(len(row["span_errors"]))

    to_average_users.append({k:np.average(v) for k,v in to_average.items()})

to_average_users.sort(key=lambda x: x["time"])
for user in to_average_users:
    print(
        f"{user['time']:.1f}s",
        f"{user['span_final']:.1f}",
        sep = " & ",
        end=" \\\\\n"
    )

print(r"\midrule")
# hack to average
user = {k:np.average([x[k] for x in to_average_users]) for k in user.keys()}
print(
        f"{user['time']:.1f}s",
        f"{user['span_final']:.1f}",
        sep = " & ",
        end=" \\\\\n"
    )
    
plot_complex(to_average_users, scheme="ESA")
