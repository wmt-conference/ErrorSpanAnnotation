import os
import json
import ipdb
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

SCHEME_ESA = "ESA"
SCHEME_MQM = "MQM"
SCHEME_GEMBA = "GEMBA"  # Schema used for parallel project, not part of WMT 2024


class AppraiseAnnotations:
    def __init__(self, path, annotation_scheme):
        self.path = path
        self.annotation_scheme = annotation_scheme
        self.df = self.load_annotations()

        # load annotators mapping
        self.annotator_mapping = pd.read_csv("data/Annotators_mapping.csv")
        # keep only AnnotatorID and login
        self.annotator_mapping = self.annotator_mapping[["AnnotatorID", "login"]]
        self.annotator_mapping["AnnotatorID"] = "Human_" + self.annotator_mapping["AnnotatorID"].astype(str)

    def load_annotations(self):
        # load csv file
        # TODO Vilem/Roman what is the purpose of (Kocmi named the columns):
        # why is the export in reverse order? I am reversing it back
        # unk_col_always_false: Kocmi didn't know what's the purpose of this column, but it is always False for all schemas
        
        header = ["login", "system", "itemID", "is_bad", "source_lang", "target_lang", "score", "documentID", "unk_col_always_false", "span_errors", "start_time", "end_time"]

        df = pd.read_csv(self.path, sep=",", names=header)
        # reverse rows order in df
        df = df.iloc[::-1].reset_index(drop=True)

        # remove rows which has "-tutorial" in the value for column system
        df = df[~df["system"].str.contains("-tutorial")]

        # remove duplicate with lower start_time, this happens when annotator changed their decision
        df = df.drop_duplicates(subset=["login", "itemID"], keep="last")
        
        return df

    def generate_scores(self):
        if not os.path.exists("data/mt-metrics-eval-v2") and os.path.exists("mt-metrics-eval-v2"):
            print("HELLO! We moved `mt-metrics-eval-v2` to `data/mt-metrics-eval-v2`. Please move the data on your system and rerun me.")
            exit()

        docs_template = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", sep="\t", header=None)
        # drop column 0
        docs_template = docs_template.drop(0, axis=1)
        # IMPORTANT: since there is a bug in batch indices, we need to map it based on the textual information

        # load mqm annotations for matching
        mqm = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.mqm.seg.score", sep="\t", header=None)
        mqm.columns = ["system", "wmt_mqm_score"]
        # generate df which for each system has the same number of rows as docs_template
        # load sources and translations
        # load sources from "mt-metrics-eval-v2/wmt23/sources/en-de.txt" and name the column sources
        protocol_annotations = []
        sources = []
        with open(f"data/mt-metrics-eval-v2/wmt23/sources/en-de.txt") as f:
            for line in f:
                sources.append(line.strip())
        for system in mqm["system"].unique():
            if system == "refA":
                translation_path = f"data/mt-metrics-eval-v2/wmt23/references/en-de.refA.txt"
            else:
                translation_path = f"data/mt-metrics-eval-v2/wmt23/system-outputs/en-de/{system}.txt"
            translation = []
            with open(translation_path) as f:
                for line in f:
                    translation.append(line.strip())
            dfcon = pd.concat([docs_template, pd.DataFrame({"source": sources, "translation": translation})], axis=1)
            dfcon['system'] = system
            protocol_annotations.append(dfcon)

        df = pd.concat(protocol_annotations).reset_index(drop=True)
        # add column with score
        df["score"] = None
        # rename column 1
        df = df.rename(columns={1: "documentID"})

        batches = json.load(open(f"campaign-ruction-rc5/data/batches_wmt23_en-de_{self.annotation_scheme.lower()}.json"))

        mapping_line_num = {}
        for batch in batches:
            for item in batch["items"]:
                if "tutorial" in item["documentID"]:
                    continue
                mapping_line_num[(item["itemID"], item["documentID"])] = (item["_item"].split(" | ")[1], item["sourceText"], item['targetText'])

        for index, row in self.df.iterrows():
            if row["is_bad"] != "TGT" or "#duplicate" in row["documentID"]:
                continue

            system = row["system"].replace("wmt23.", "")
            documentID = row["documentID"].split("#")[0]
            line_num, source, translation = mapping_line_num[(row["itemID"], row["documentID"])]
            score = row["score"]
            if self.annotation_scheme == SCHEME_MQM:
                # parse json from row['span_errors']
                score = 0
                weight = {"minor": -1, "major": -5, "critical": -25}
                span_errors = json.loads(row['span_errors'])
                for error in span_errors:
                    if "Punctuation" in error['error_type']:
                        score += -0.1
                    else:
                        score += weight[error["severity"]]

            assigned = df.loc[(df["system"] == system) & (df["documentID"] == documentID) & (df["source"] == source) & (df["translation"] == translation)]

            if row["documentID"] == 'elitr_minuting-19#GPT4-5shot' and row['login'] in ["engdeu6907", "engdeu6807", "engdeu6a07"]:
                # bug in campaign rc5
                if row["itemID"] == 90:
                    assigned = df.loc[[955]]
                else:
                    assigned = df.loc[[956]]
                
            if len(assigned) != 1:
                if (documentID == "manlycoffee.110351250115060992"):
                    try: 
                        mapping_line_num[(row["itemID"] + 4, row["documentID"])]
                        index_number = assigned.index[1]
                    except:
                        index_number = assigned.index[0]
                    # print(system, index_number, index, df.loc[index_number, "score"])
                    if system == "ONLINE-W":
                        if row['login'] == "engdeu6908":
                            index_number = 5286
                        else:
                            index_number = 5290
                else:
                    ipdb.set_trace()
            else:
                index_number = assigned.index[0]

                
            assigned_score = df.loc[index_number, "score"]
            # assign score to the correct row in df, first check if the row is None
            if assigned_score is None or assigned_score == score:
                df.loc[index_number, "score"] = score
            else:
                print("there is a problem, which needs investigation")
                ipdb.set_trace()

        # combine columns from df and mqm on their index
        df = df.merge(mqm, left_index=True, right_index=True, how="left")
        # keep only column system_x and score
        df = df[["system_x", "score"]]
        # rename system_x to system
        df = df.rename(columns={"system_x": "system"})
        # replace None scores with "None"
        df["score"] = df["score"].fillna("None")
        # save df into tsv file
        df.to_csv(f"campaign-ruction-rc5/en-de.{self.annotation_scheme}.seg.score", sep="\t", index=False, header=False)

        # allows chaining
        return self


    def get_average_minutes_per_HIT(self, unfiltered=False):
        median = 0
        if unfiltered:
            # use the raw time between first annotation and the last annotation
            df = self.df.groupby("login").agg({"start_time": "min", "end_time": "max"})
            df["time"] = (df["end_time"] - df["start_time"]) / 60
        else:
            # remove wait times between documents
            # plot_annotation_times(self.df, "all_raw", self.annotation_scheme)

            annot_times = []
            for login in self.df.login.unique():
                df = self.df[self.df['login'] == login]
                # sort by start_time
                df = df.sort_values("start_time").reset_index(drop=True)
                # TODO Vilem/Roman: # why some HITs looks like the annotator first annotated the second half of the HIT and then the first half? like ESA-engdeu691a
                for i in range(0, len(df) - 1):
                    annot_time = df.iloc[i + 1]["start_time"] - df.iloc[i]["start_time"]
                    annot_times.append(annot_time)
            df = pd.DataFrame(annot_times).sort_values(by=0)
            quantile = df.quantile(0.95)[0]
            median = df.median()[0]

            df = self.df.sort_values("start_time")
            for login in self.df.login.unique():
                subdf = df[df['login'] == login]
                reducing_time = 0
                previous_timestamp = subdf.iloc[0]["start_time"]
                for i in range(1, len(subdf)):
                    index = subdf.index[i]

                    # if time diff is larger than 95% quantile, then we assume that the annotator was not annotating and
                    # we replace the start_time with previous start_time + median time
                    diff = df.loc[index]["start_time"] - previous_timestamp
                    if diff > quantile:
                        reducing_time += diff - median

                    previous_timestamp = df.loc[index]["start_time"]
                    df.at[index, "start_time"] = df.loc[index]["start_time"] - reducing_time

            # plot_annotation_times(df, "removed_waitings", self.annotation_scheme)

            df['max_time'] = df['start_time']
            df = df.groupby("login").agg({"start_time": "min", "max_time": "max"})
            df["time"] = (df["max_time"] - df["start_time"]) / 60

        self.plot_average_minutes_per_HIT(df)

        return df["time"].mean(), median

    def plot_average_minutes_per_HIT(self, df):
        # add column with AnnotatorIDs where login is the key
        df = df.merge(self.annotator_mapping, left_index=True, right_on="login", how="left")
        # sort the time
        df = df.sort_values("time").reset_index(drop=True)

        # plot the time as bar chart, use index of df as an x-axis. Then for each AnnotatorID, print only the bars for its AnnotatorID
        colors = plt.cm.jet(np.linspace(0, 1, df['AnnotatorID'].nunique()))
        color_map = {id: color for id, color in zip(df['AnnotatorID'].unique(), colors)}
        plt.clf()
        plt.figure(figsize=(10, 6))
        for index, row in df.iterrows():
            plt.bar(index, row['time'], color=color_map[row['AnnotatorID']], label=row['AnnotatorID'])

        # This part ensures that each AnnotatorID is only added once to the legend.
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())
        plt.xticks(df.index)  # Ensure x-ticks match your indices.
        plt.ylabel("Time in minutes")
        plt.title(self.annotation_scheme)
        # save into "generated_plots" folder
        plt.savefig(f"generated_plots/Avg_times_{self.annotation_scheme}.png")


def plot_annotation_times(all_df, name, annotation_scheme):
    if not os.path.exists(f"generated_plots/Annotation_styles/{name}"):
        os.makedirs(f"generated_plots/Annotation_styles/{name}")
    
    for login in all_df.login.unique():
        df = all_df[all_df['login'] == login]

        # subtrack the start_time of the first row from all
        pd.options.mode.chained_assignment = None
        df["start_time"] = (df["start_time"] - df["start_time"].iloc[0]) / 60


        # plot column "start_time" as scatter plot
        plt.clf()
        plt.figure(figsize=(10, 6))
        plt.scatter(df.index, df["start_time"])
        # add title
        plt.title(f"How {login} annotator have been annotating HIT. We need to remove the wait times")
        # add axis label
        plt.ylabel("Start time for annotation")
        plt.xlabel("Annotation ID")
        # save plot into generated_plots
        plt.savefig(f"generated_plots/Annotation_styles/{name}/{annotation_scheme}_{login}.png")