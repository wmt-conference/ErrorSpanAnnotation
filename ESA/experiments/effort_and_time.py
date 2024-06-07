from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=False).dropna()
import numpy as np
import collections
import matplotlib.pyplot as plt
import ESA.figutils as figutils
import ESA.settings

figutils.matplotlib_default()

def get_averages(protocol):
    to_average_users = []
    for _, local in df.groupby(f"{protocol}_AnnotatorID"):
        to_average = collections.defaultdict(list)
        time_median = np.median(local[f"{protocol}_duration_seconds"])
        for _, row in local.iterrows():
            if row[f"{protocol}_duration_seconds"] > 60*5:
                to_average["time"].append(time_median)
            else:
                to_average["time"].append(row[f"{protocol}_duration_seconds"])
            to_average["span_gemba"].append(len(row["LLM_error_spans"]))
            to_average["span_kept"].append(len([
                a for a in row["LLM_error_spans"]
                if [b for b in row[f"{protocol}_error_spans"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
            ]))
            to_average["span_removed"].append(len([
                a for a in row["LLM_error_spans"]
                if not [b for b in row[f"{protocol}_error_spans"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
            ]))
            to_average["span_added"].append(len([
                a for a in row[f"{protocol}_error_spans"]
                if not [b for b in row["LLM_error_spans"] if a["start_i"] == b["start_i"] and a["end_i"] == b["end_i"] and a["severity"] == b["severity"]]
            ]))

            to_average["span_final"].append(len(row[f"{protocol}_error_spans"]))

        to_average_users.append({k:np.average(v) for k,v in to_average.items()})
    return to_average_users

data_esaai = get_averages("ESAAI-1") + get_averages("ESAAI-2")
data_esa = get_averages("ESA-1") + get_averages("ESA-2")

user = {k:np.average([x[k] for x in data_esaai]) for k in data_esaai[0].keys()}
print(
    "ESAAI",
    f"{user['time']:.1f}s",
    f"{user['time']/user['span_final']:.1f}s/span",
    f"{user['span_gemba']:.1f}",
    f"{user['span_kept']:.1f}",
    f"{user['span_removed']:.1f}",
    f"{user['span_added']:.1f}",
    f"{user['span_final']:.1f}",
    sep = " & ",
    end=" \\\\\n"
)
user = {k:np.average([x[k] for x in data_esa]) for k in data_esa[0].keys()}
print(
    "ESA  ",
    f"{user['time']:.1f}s",
    f"{user['time']/user['span_final']:.1f}s/span",
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
    to_average_users.sort(key=lambda x: x["time"])

    if scheme == "ESAAI":
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
    ax1.set_ylabel("Time", labelpad=-2)
    ax1.set_xlabel(f"User ({scheme.replace('ESAAI', ESA.settings.METHODS['esaai']['name'])})")
    ax1.set_xticks(range(len(to_average_users)), [""]*len(to_average_users))
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.set_ylim(0, 100)
    avg_time = np.average([x["time"] for x in to_average_users])
    ax1.axhline(y=np.average([x["time"] for x in to_average_users]), color="black", linestyle="--")
    ax1.text(
        x=0, y=avg_time+4,
        s=f"{avg_time:.1f}s",
    )

    plt.tight_layout(pad=0.1)
    plt.savefig(f"PAPER_ESAAI/generated_plots/effort_and_time_{scheme}.pdf")
    plt.show()
        
plot_complex(data_esaai, scheme="ESAAI")
plot_complex(data_esa, scheme="ESA")
