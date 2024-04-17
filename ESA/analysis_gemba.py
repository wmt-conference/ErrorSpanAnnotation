from annotations import AppraiseAnnotations
import numpy as np
import collections

anno = AppraiseAnnotations.get_full("GEMBA")

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
        if type(row["span_errors_orig"]) is float or type(row["span_errors"]) is float:
            continue

        v_time = row["start_time"]-prev_time
        if v_time > v_time_quantile or v_time <= 0:
            v_time = v_time_median
        prev_time = row["start_time"]
        to_average["time"].append(v_time)
        to_average["span_orig"].append(len(row["span_errors_orig"]))
        to_average["span_kept"].append(len([
            a for a in row["span_errors_orig"]
            if [b for b in row["span_errors"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
        ]))
        to_average["span_removed"].append(len([
            a for a in row["span_errors_orig"]
            if not [b for b in row["span_errors"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
        ]))
        to_average["span_added"].append(len([
            a for a in row["span_errors"]
            if not [b for b in row["span_errors_orig"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
        ]))

        to_average["span_final"].append(len(row["span_errors"]))

    to_average_users.append({k:np.average(v) for k,v in to_average.items()})

to_average_users.sort(key=lambda x: x["time"])
for user in to_average_users:
    print(
        f"{user['time']:.1f}s",
        f"{user['span_orig']:.1f}",
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
    f"{user['span_orig']:.1f}",
    f"{user['span_kept']:.1f}",
    f"{user['span_removed']:.1f}",
    f"{user['span_added']:.1f}",
    f"{user['span_final']:.1f}",
    sep = " & ",
    end=" \\\\\n"
)
    

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
    