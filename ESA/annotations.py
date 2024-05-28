import os
import json
import ipdb
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

SCHEME_ESA = "ESA"
SCHEME_MQM = "MQM"
SCHEME_ESA_SEVERITY = "ESA_SEVERITY" # protocol where score is devised from severity of errors

SCHEME_GEMBA = "GEMBA"  # Schema used for parallel project, not part of WMT 2024
SCHEME_GEMBA_SEVERITY = "GEMBA_SEVERITY"  # Schema used for parallel project, not part of WMT 2024

MQM_WEIGHTS = {"minor": -1, "major": -5, "critical": -25, "undecided": 0}


def apply_mqm_annotations(span_errors):
    # missing values needs to be None
    if not isinstance(span_errors, list):
        return "None"

    score = 0
    for error in span_errors:
        score += MQM_WEIGHTS[error["severity"]]
    if score < -25:
        score = -25
    return score

class AppraiseAnnotations:
    def __init__(self, annotation_scheme):
        self.batch_file_name = annotation_scheme
        if "_SEVERITY" in annotation_scheme:
            self.batch_file_name = annotation_scheme.replace('_SEVERITY', '')

        self.annotation_scheme = annotation_scheme
        self.df = self.load_annotations()
        self._estimate_annotation_duration()

        # load annotators mapping
        self.annotator_mapping = pd.read_csv("data/Annotators_mapping.csv")
        # keep only AnnotatorID and login
        self.annotator_mapping = self.annotator_mapping[["AnnotatorID", "login"]]
        self.annotator_mapping["AnnotatorID"] = "Human_" + self.annotator_mapping["AnnotatorID"].astype(str)

        # to the df add column with AnnotatorID where login is the key
        self.df = self.df.merge(self.annotator_mapping, left_on="login", right_on="login", how="left")
        # unk_col_always_false: unclear what the purpose of this constant column is
        self.df = self.df.drop(columns=["unk_col_always_false"])
        # add column bad_duplicate to filter out bad and duplicate rows
        self.df["valid_segment"] = self.df.apply(lambda x: "#bad" not in x['documentID'] and "#duplicate" not in x['documentID'], axis=1)


    def load_annotations(self):
        # load csv file        
        header = ["login", "system", "itemID", "is_bad", "source_lang", "target_lang", "score", "documentID", "unk_col_always_false", "span_errors", "start_time", "end_time"]

        df = pd.read_csv(f"campaign-ruction-rc5/240315rc5{self.batch_file_name}.scores.csv", sep=",", names=header)
        # reverse rows order in df
        df = df.iloc[::-1].reset_index(drop=True)

        # remove rows which has "-tutorial" in the value for column system
        df = df[~df["system"].str.contains("-tutorial")]

        # remove duplicate with lower start_time, this happens when annotator changed their decision
        df = df.drop_duplicates(subset=["login", "itemID"], keep="last")

        # generate scores for MQM schemas
        if self.annotation_scheme in [SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA_SEVERITY]:
            for index, row in df.iterrows():
                score = 0
                span_errors = json.loads(row['span_errors'])
                for error in span_errors:
                    if self.annotation_scheme == SCHEME_MQM and "Punctuation" in error['error_type']:
                        score += -0.1
                    else:
                        score += MQM_WEIGHTS[error["severity"]]
                if score < -25:
                    score = -25
                df.at[index, "score"] = score                

        return df
    
    def _estimate_annotation_duration(self): 
        self.df["duration_seconds"] = 0       
        for login in self.df.login.unique():
            subdf = self.df[self.df['login'] == login]
            previous_timestamp = subdf.iloc[0]["start_time"]
            for i in range(1, len(subdf)):
                index = subdf.index[i]
                diff = self.df.loc[index]["start_time"] - previous_timestamp
                
                previous_timestamp = self.df.loc[index]["start_time"]
                self.df.at[index, "duration_seconds"] = diff   

    @staticmethod
    def get_full(annotation_scheme):
        print("WARNING: You are using a deprecated loader. Please switch to `MergedAnnotations().df`")
        fname = f"campaign-ruction-rc5/en-de.{annotation_scheme}.pkl"
        if not os.path.exists(fname):
            print("Generating data")
            anno = AppraiseAnnotations(annotation_scheme).add_gemba_and_wmt_scores()
            anno.df.to_pickle(fname)
        return pd.read_pickle(fname)
    
    def add_gemba_and_wmt_scores(self):
        print("WARNING: You are using a deprecated loader. Please switch to `MergedAnnotations().df`")
        # WARNING: Before you delete me, please check that `analysis_document_speedup.py` and `analysis_edit_degree.py` have been migrated to the new loader.

        lines_score = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.mqm.seg.score", sep="\t", header=None, dtype=str)
        lines_score.columns = ["systemID", "wmt_mqm_score"]
        lines_score = lines_score.drop(columns=["systemID"])
        lines_mqm = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.mqm.merged.seg.rating", sep="\t", header=None, dtype=str)
        lines_mqm.columns = ["systemID", "wmt_mqm"]
        lines_mqm = lines_mqm[lines_mqm["systemID"] != "synthetic_ref"]
        systems = list(lines_mqm["systemID"].unique())
        lines_mqm = lines_mqm.drop(columns=["systemID"])

        lines_source = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/sources/en-de.txt", sep="\t", header=None, dtype=str)
        lines_source.columns = ["src"]
        lines_docs = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", sep="\t", header=None, dtype=str)
        lines_docs.columns = ["domain", "documentID"]

        annotations_all = []
        for system in systems:
            if system == "refA":
                fname = f"data/mt-metrics-eval-v2/wmt23/references/en-de.refA.txt"
            else:
                fname = f"data/mt-metrics-eval-v2/wmt23/system-outputs/en-de/{system}.txt"
            lines_translation = pd.read_csv(fname, sep="\t", header=None)
            lines_translation.columns = ["tgt"]
            
            dfcon = pd.concat([lines_docs, lines_translation, lines_source, pd.DataFrame([str(x) for x in range(len(lines_source))], columns=["itemID_wmt"])], axis=1)
            dfcon["systemID"] = system
            annotations_all.append(dfcon)

        wmt_df = pd.concat(annotations_all).reset_index(drop=True)

        assert len(wmt_df) == len(lines_score)
        assert len(wmt_df) == len(lines_mqm)
        wmt_df = wmt_df.merge(lines_score, left_index=True, right_index=True, how="left")
        wmt_df = wmt_df.merge(lines_mqm, left_index=True, right_index=True, how="left")

        # hack because 
        wmt_df["systemID"] 

        batches = json.load(open(f"campaign-ruction-rc5/data/batches_wmt23_en-de_{self.batch_file_name.lower()}.json"))
        batches = [
            item for task in batches for item in task["items"]
            if "_item" in item
        ]
        for item in batches:
            tmp = item["documentID"].split("#")
            item["documentID"], item["systemID"] = tmp[0], tmp[1]
            if len(tmp) > 2:
                item["documentID_suffix"] = tmp[2]
        batches = pd.DataFrame.from_dict(batches)

        self.df["span_errors_gemba"] = None
        self.df["span_errors_wmt"] = None
        self.df["score_wmt"] = None

        for row_index, row in self.df.iterrows():
            itemID = row["itemID"]
            tmp = row["documentID"].split("#")
            documentID, systemID = tmp[0], tmp[1]

            item_batch = batches[(batches["itemID"] == itemID) & (batches["documentID"] == documentID) & (batches["systemID"] == systemID)]
            if len(item_batch) != 1:
                print(f"FOUND IN BATCHES ({len(item_batch)})", itemID, documentID, systemID)
                continue
            item_batch = item_batch.iloc[0]
            itemID_wmt = item_batch["_item"].split(" | ")[1]

            item_wmt = wmt_df[(wmt_df["itemID_wmt"] == itemID_wmt) & (wmt_df["documentID"] == documentID) & (wmt_df["systemID"] == systemID)]

            if len(item_wmt) != 1:
                print(f"FOUND IN WMT ({len(item_wmt)})", itemID, itemID_wmt, documentID, systemID, sep="^")
                continue

            # merge
            self.df.at[row_index, 'span_errors_gemba'] = item_batch["mqm"]
            self.df.at[row_index, 'span_errors_wmt'] = item_wmt["wmt_mqm"]
            self.df.at[row_index, 'score_wmt'] = item_wmt["wmt_mqm_score"]
            # answers are encoded in stringified JSON
            self.df.at[row_index, 'span_errors'] = json.loads(row["span_errors"])

        return self

    def generate_wmt_score_files(self):
        docs_template = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", sep="\t", header=None)
        # drop column 0
        docs_template = docs_template.drop(0, axis=1)
        # IMPORTANT: since there is a bug in batch indices, we need to map it based on the textual information

        # load mqm annotations for matching
        mqm = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.mqm.seg.score", sep="\t", header=None)
        mqm.columns = ["system", "wmt_mqm_score"]

        mqm_spans = pd.read_csv(f"data/wmt23_en-de.mqm.merged_sorted.seg.rating", sep="\t", header=None)
        mqm_spans.columns = ["system", "wmt_mqm_error_spans"]

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

        batches = json.load(open(f"campaign-ruction-rc5/data/batches_wmt23_en-de_{self.batch_file_name.lower()}.json"))

        mapping_line_num = {}
        for batch in batches:
            for item in batch["items"]:
                if "tutorial" in item["documentID"]:
                    continue

                if "GEMBA" in self.annotation_scheme:
                    mapping_line_num[(item["itemID"], item["documentID"])] = (item["_item"].split(" | ")[1], item["sourceText"], item['targetText'], item['mqm'])
                else:
                    mapping_line_num[(item["itemID"], item["documentID"])] = (item["_item"].split(" | ")[1], item["sourceText"], item['targetText'], None)

        for index, row in self.df.iterrows():
            if row["is_bad"] != "TGT" or "#duplicate" in row["documentID"]:
                continue

            system = row["system"].replace("wmt23.", "")
            documentID = row["documentID"].split("#")[0]
            line_num, source, translation, orig_mqm = mapping_line_num[(row["itemID"], row["documentID"])]
            score = row["score"]

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
                # ipdb.set_trace()

            # assign source and system into the df
            self.df.at[index, "source_seg"] = assigned['source'].iloc[0]
            self.df.at[index, "translation_seg"] = assigned['translation'].iloc[0]

            if "GEMBA" in self.annotation_scheme:
                self.df.at[index, "gemba_mqm_span_errors"] = orig_mqm
                df.loc[index_number, "gemba_mqm_span_errors"] = orig_mqm

            if self.annotation_scheme == "MQM":
                if 'wmt_mqm_span_errors' not in self.df:
                    self.df['wmt_mqm_span_errors'] = None

                spans = mqm_spans.iloc[index_number]["wmt_mqm_error_spans"]
                if spans == "None":
                    spans = "None"
                else:
                    spans = json.loads(spans)
                    if "errors" in spans:
                        spans = spans["errors"]

                # asign list into the df under column wmt_mqm_span_errors into the row index
                self.df.at[index, "wmt_mqm_span_errors"] = spans

        # combine columns from df and mqm on their index
        df = df.merge(mqm, left_index=True, right_index=True, how="left")

        # also save scores as if the original LLM scores were generated
        if "GEMBA" in self.annotation_scheme:
            df2 = df.copy()
            df2['score'] = df2['gemba_mqm_span_errors'].apply(lambda x: apply_mqm_annotations(x))
            df2 = df2[["system_x", "score"]]
            df2.to_csv(f"campaign-ruction-rc5/en-de.LLM.seg.score", sep="\t", index=False, header=False)
            
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
