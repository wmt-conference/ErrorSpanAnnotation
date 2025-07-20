import os
import ipdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from ESA.utils import PROTOCOL_DEFINITIONS
from ESA.annotation_loader import AnnotationLoader


def get_average_minutes_per_HIT(orig_df, protocol, unfiltered=False):
    median = 0
    if unfiltered:
        # use the raw time between first annotation and the last annotation
        df = orig_df.groupby(f"{protocol}_login").agg({f"{protocol}_start_time": "min", f"{protocol}_end_time": "max"})
        df["time"] = (df[f"{protocol}_end_time"] - df[f"{protocol}_start_time"]) / 60
    else:
        # remove wait times between documents
        # plot_annotation_times(orig_df, "all_raw", protocol)

        annot_times = []
        for login in orig_df[f"{protocol}_login"].unique():
            subdf = orig_df[orig_df[f"{protocol}_login"] == login]
            # sort by start_time
            subdf = subdf.sort_values(f"{protocol}_start_time").reset_index(drop=True)
            for i in range(0, len(subdf) - 1):
                annot_time = subdf.iloc[i + 1][f"{protocol}_start_time"] - subdf.iloc[i][f"{protocol}_start_time"]
                annot_times.append(annot_time)
        df = pd.DataFrame(annot_times).sort_values(by=0)
        quantile = df.quantile(0.95)[0]
        median = df.median()[0]

        lengths = {}

        for login in orig_df[f"{protocol}_login"].unique():
            total_time = 0
            subdf = orig_df[orig_df[f"{protocol}_login"] == login]
            subdf = subdf.sort_values(f"{protocol}_start_time").reset_index(drop=True)
            for i in range(1, len(subdf)):
                index = subdf.index[i]
                prev_index = subdf.index[i - 1]
                # if time diff is larger than 95% quantile, then we assume that the annotator was not annotating and
                # we replace the start_time with previous start_time + median time
                diff = subdf.loc[index][f"{protocol}_start_time"] - subdf.loc[prev_index][f"{protocol}_start_time"]
                if diff > quantile:
                    diff = median

                total_time += diff
            lengths[login] = total_time / 60
        df = pd.DataFrame.from_dict(lengths, orient='index', columns=["time"])

    plot_average_minutes_per_HIT(df, orig_df, protocol, median)
    return df["time"].mean(), median


def plot_average_minutes_per_HIT(df, orig_df, protocol, median_time):
    annotator_mapping = orig_df[[f"{protocol}_login", f"{protocol}_AnnotatorID"]].drop_duplicates().set_index(f"{protocol}_login")
    df = df.merge(annotator_mapping, left_index=True, right_on=f"{protocol}_login", how="left")
    # sort the time
    df = df.sort_values("time").reset_index(drop=True)
    median_annot = df["time"].median()

    # plot the time as bar chart, use index of df as an x-axis. Then for each AnnotatorID, print only the bars for its AnnotatorID
    colors = plt.cm.jet(np.linspace(0, 1, df[f"{protocol}_AnnotatorID"].nunique()))
    color_map = {id: color for id, color in zip(df[f"{protocol}_AnnotatorID"].unique(), colors)}
    plt.clf()
    plt.figure(figsize=(10, 6))
    for index, row in df.iterrows():
        plt.bar(index, row['time'], color=color_map[row[f"{protocol}_AnnotatorID"]], label=row[f"{protocol}_AnnotatorID"])

    # This part ensures that each AnnotatorID is only added once to the legend.
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    plt.xticks(df.index)  # Ensure x-ticks match your indices.
    plt.ylabel("Time in minutes")
    plt.title(f"Total time for HIT ({protocol}). Median time per HIT: {median_annot:.1f} min (per annotation {median_time:.0f} s)")
    plt.ylim(0, 140)

    plt.savefig(f"generated_plots/Avg_times_{protocol}.png")


def plot_annotation_times(all_df, name, protocol):
    all_df = all_df.copy()
    if not os.path.exists(f"generated_plots/Annotation_styles/{name}"):
        os.makedirs(f"generated_plots/Annotation_styles/{name}")

    for login in all_df[f"{protocol}_login"].unique():
        df = all_df[all_df[f"{protocol}_login"] == login]

        # subtrack the start_time of the first row from all
        pd.options.mode.chained_assignment = None
        df[f"{protocol}_start_time"] = (df[f"{protocol}_start_time"] - df[f"{protocol}_start_time"].iloc[0]) / 60

        # plot column "start_time" as scatter plot
        plt.clf()
        plt.figure(figsize=(10, 6))
        plt.scatter(df.index, df[f"{protocol}_start_time"])
        # add title
        plt.title(f"How {login} annotator have been annotating HIT. We need to remove the wait times")
        # add axis label
        plt.ylabel("Start time for annotation")
        plt.xlabel("Annotation ID")
        # save plot into generated_plots
        plt.savefig(f"generated_plots/Annotation_styles/{name}/{protocol}_{login}.png")


def analyse_annotation_durations(df, protocol):
    median = df[f"{protocol}_duration_seconds"].median()

    # calculate median time per annotator
    times = []
    for annotator in df[f"{protocol}_AnnotatorID"].unique():
        times.append(df[df[f"{protocol}_AnnotatorID"] == annotator][f"{protocol}_duration_seconds"].median())

    # print makro average of median times
    print(f"Average median time per segment for {protocol}: {np.mean(times):.1f} s (makro: {median:.1f} s)")

def avg_time_per_word(df, protocol):
    df = df.copy()
    # calculate average time per word
    df[f"{protocol}_time_per_word"] = df[f"{protocol}_duration_seconds"] / df[f"word_count"]
    words_per_hour = 3600 / df[f"{protocol}_time_per_word"].median()
    print(f"Median time per word for {protocol}: {df[f'{protocol}_time_per_word'].median():.2f} s. That is {words_per_hour:.0f} words per hour.")

def AvgTimePerWord():
    annotations_loader = AnnotationLoader(refresh_cache=False)
    df = annotations_loader.get_view(only_overlap=True)
    df["word_count"] = df['hypothesis'].apply(lambda x: len(x.split(" ")))


    for protocol in ['MQM-1', 'ESA-1', 'ESAAI-1']:
        times = get_average_minutes_per_HIT(df, protocol)
        print(f"Protocol: {protocol}, Average time per HIT: {times[0]:.1f} minutes, Median time per HIT: {times[1]:.1f} seconds")

        analyse_annotation_durations(df, protocol)

        avg_time_per_word(df, protocol)
        counts = []
        for login in df[f"{protocol}_login"].unique():
            subdf = df[df[f"{protocol}_login"] == login]
            count_words = subdf["word_count"].sum()
            counts.append(count_words)
        counts_df = pd.DataFrame(counts)
        print(f"Minimum words per HIT: {counts_df.min()[0]}, Maximum words per HIT: {counts_df.max()[0]}")




if __name__ == '__main__':
    AvgTimePerWord()
