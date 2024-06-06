import ipdb
import json
import pandas as pd


PROTOCOL_DEFINITIONS = {
    'MQM-1': {
        "framework": "appraise",
        "appraise_scorefile": "240315rc5MQM.scores.csv",
        "appraise_batchefile": "batches_wmt23_en-de_mqm.json",
    },
    'ESA-1': {
        "framework": "appraise",
        "appraise_scorefile": "240315rc5ESA.scores.csv",
        "appraise_batchefile": "batches_wmt23_en-de_esa.json",
    },
    'ESAAI-1': {
        "framework": "appraise",
        "appraise_scorefile": "240315rc5GEMBA.scores.csv",
        "appraise_batchefile": "batches_wmt23_en-de_gemba.json",
    },
    'ESA-2': {
        "framework": "appraise",
        "appraise_scorefile": "240520rc6ESA.scores.csv",
        "appraise_batchefile": "batches_wmt23_en-de_esa.json",
    },
    'ESAAI-2': {
        "framework": "appraise",
        "appraise_scorefile": "240520rc6GEMBA.scores.csv",
        "appraise_batchefile": "batches_wmt23_en-de_gemba.json",
    },
    'WMT-MQM': {
        "framework": "wmt",
    },
    'WMT-DASQM': {
        "framework": "wmt",
    },
    'LLM': {
        "framework": "llm",
    }
}

def read_json_spans(spans):
    if spans == "None":
        return None
    spans = json.loads(spans)
    if "errors" in spans:
        return spans["errors"]
    return spans


def load_raw_wmt(protocol):
    docs_template = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", sep="\t", header=None, dtype=str)
    docs_template.columns = ["domainID", "documentID"]

    protocolname = "mqm" if protocol == "WMT-MQM" else "da-sqm"
    human_annotations = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.{protocolname}.seg.score", sep="\t", header=None, dtype=str)
    human_annotations.columns = ["systemID", "score"]

    systems = human_annotations["systemID"].unique()

    # load sources and translations
    protocol_annotations = []
    sources = []

    with open(f"data/mt-metrics-eval-v2/wmt23/sources/en-de.txt") as f:
        for line in f:
            sources.append(line.strip())
    for system in systems:
        if system == "refA":
            translation_path = f"data/mt-metrics-eval-v2/wmt23/references/en-de.refA.txt"
        else:
            translation_path = f"data/mt-metrics-eval-v2/wmt23/system-outputs/en-de/{system}.txt"
        translation = []
        with open(translation_path) as f:
            for line in f:
                translation.append(line.strip())

        dfcon = pd.concat([docs_template, pd.DataFrame({"source": sources, "hypothesis": translation})], axis=1)
        dfcon['systemID'] = system
        dfcon['sourceID'] = range(len(dfcon))

        protocol_annotations.append(dfcon)

    df = pd.concat(protocol_annotations).reset_index(drop=True)
    # df['hypothesisID'] = df['sourceID'] + "#" + df['documentID'] + "#" + df['systemID']
    df['hypothesisID'] = df.apply(lambda x: f"{x['sourceID']}#{x['documentID']}#{x['systemID']}", axis=1)

    # map scores to df, but check that files are sorted in the same way
    assert (human_annotations['systemID'] == df['systemID']).all()
    df['score'] = human_annotations['score']

    # for mqm protocol, load ratings
    if protocol == "WMT-MQM":
        ratings = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.mqm.merged.seg.rating", sep="\t", header=None, dtype=str)
        ratings.columns = ["systemID", "error_spans"]
        ratings = ratings[ratings["systemID"] != "synthetic_ref"].reset_index(drop=True)
        ratings["documentID"] = df['documentID']
        ratings["sourceID"] = df['sourceID']
        ratings['hypothesisID'] = ratings.apply(lambda x: f"{x['sourceID']}#{x['documentID']}#{x['systemID']}", axis=1)
        # make hypothesisID index
        ratings = ratings.set_index('hypothesisID')
        df['error_spans'] = df.apply(lambda x: ratings.loc[x['hypothesisID'], 'error_spans'], axis=1)
        df['error_spans'] = df['error_spans'].apply(lambda x: read_json_spans(x))

    return df


def load_raw_appraise_campaign(protocol):
    appraise_batches = json.load(open(f"campaign-ruction-rc5/data/{PROTOCOL_DEFINITIONS[protocol]['appraise_batchefile']}"))

    ipdb.set_trace()

    docs_template = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", sep="\t", header=None)
    # drop column 0, which is domain
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


    mapping_line_num = {}
    for batch in appraise_batches:
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

        if row["documentID"] == 'elitr_minuting-19#GPT4-5shot' and row['login'].endswith("07"):
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
                    if row['login'] in ["engdeu6908", "engdeu6e08"]:
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
            if 'gemba_mqm_span_errors' not in self.df:
                self.df['gemba_mqm_span_errors'] = [[] for _ in range(len(self.df))]
                df['gemba_mqm_span_errors'] = [[] for _ in range(len(df))]

            if len(orig_mqm) > 0:
                self.df.at[index, "gemba_mqm_span_errors"] = orig_mqm
                df.loc[index_number, "gemba_mqm_span_errors"] = orig_mqm


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
