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
        "framework": "appraise",
        "appraise_scorefile": "240315rc5GEMBA.scores.csv",
        "appraise_batchefile": "batches_wmt23_en-de_gemba.json",
    }
}


MQM_WEIGHTS = {"minor": -1, "major": -5, "critical": -25, "undecided": 0}


def apply_mqm_scoring(span_errors):
    # missing values needs to be None
    if not isinstance(span_errors, list):
        return "None"

    score = 0
    for error in span_errors:
        if "error_type" in error and "Punctuation" in error['error_type']:
            score += -0.1
        else:
            score += MQM_WEIGHTS[error["severity"]]
    if score < -25:
        score = -25
    return float(score)


def read_json_spans(spans):
    try:
        spans = json.loads(spans)
    except:
        return None

    if "errors" in spans:
        return spans["errors"]
    return spans


def load_raw_wmt(protocol):
    docs_template = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", sep="\t", header=None, dtype=str)
    docs_template.columns = ["domainID", "documentID"]

    protocolname = "mqm" if protocol == "WMT-MQM" else "da-sqm"
    human_annotations = pd.read_csv(f"data/mt-metrics-eval-v2/wmt23/human-scores/en-de.{protocolname}.seg.score", sep="\t", header=None, dtype=str)
    human_annotations.columns = ["systemID", "score"]

    # systems = human_annotations["systemID"].unique()
    # we have to hardwire the order to avoid problems in the future
    systems = ['AIRC', 'GPT4-5shot', 'Lan-BridgeMT', 'NLLB_Greedy', 'NLLB_MBR_BLEU', 'ONLINE-A', 'ONLINE-B', 'ONLINE-G', 'ONLINE-M', 'ONLINE-W', 'ONLINE-Y', 'ZengHuiMT', 'refA']

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
        dfcon['score'] = human_annotations[human_annotations['systemID'] == system]['score'].values

        protocol_annotations.append(dfcon)

    df = pd.concat(protocol_annotations).reset_index(drop=True)
    # df['hypothesisID'] = df['sourceID'] + "#" + df['documentID'] + "#" + df['systemID']
    df['hypothesisID'] = df.apply(lambda x: f"{x['sourceID']}#{x['documentID']}#{x['systemID']}", axis=1)

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

    # convert score to float
    df['score'] = df['score'].replace("None", float("nan")).astype(float)

    return df


def load_raw_appraise_campaign(protocol):
    appraise_batches = json.load(open(f"campaign-ruction-rc5/data/{PROTOCOL_DEFINITIONS[protocol]['appraise_batchefile']}"))

    mapping_line_num = {}
    for batch in appraise_batches:
        for item in batch["items"]:
            if "tutorial" in item["documentID"]:
                itemids = ["", item["itemID"], ""]
            else:
                itemids = item["_item"].split(" | ")

            itemid = f"{item['itemID']}#{item['documentID']}"

            if item["documentID"] == 'elitr_minuting-19#GPT4-5shot':
                # bug in campaign rc5, one document was split between two accounts, but itemIDs overlapped
                if "398" in item['_item']:
                    itemid = "bug1"
                elif "399" in item['_item']:
                    itemid = "bug2"

            if protocol == "LLM":
                mapping_line_num[itemid] = [itemids[1], item["sourceText"], item['targetText'], json.dumps(item['mqm'])]
            else:
                mapping_line_num[itemid] = [itemids[1], item["sourceText"], item['targetText'], "None"]

    header = ["login", "system", "itemID", "is_bad", "source_lang", "target_lang", "score", "documentID", "unk_col_always_false", "error_spans", "start_time", "end_time"]
    scores = pd.read_csv(f"campaign-ruction-rc5/{PROTOCOL_DEFINITIONS[protocol]['appraise_scorefile']}", sep=",", names=header, dtype=str)

    df = load_raw_wmt("WMT-DASQM")
    df['score'] = "None"

    for index, row in scores.iterrows():
        if "#duplicate" in row["documentID"] or "tutorial" in row["documentID"]:
            # duplicate are used to fill documents to have exactly 100 items. It is fine to skip them
            continue

        itemid = f"{row['itemID']}#{row['documentID']}"

        if row["documentID"] == 'elitr_minuting-19#GPT4-5shot' and row['login'].endswith("07"):
            if row["itemID"] == "90":
                itemid = "bug1"
            elif row["itemID"] == "91":
                itemid = "bug2"

        item = mapping_line_num[itemid]
        hypothesisID = f"{item[0]}#{row['documentID']}"

        if row["is_bad"] != "TGT":
            data = {"hypothesisID": hypothesisID,
                     "is_bad": row["is_bad"],
                     "source": item[1],
                     "hypothesis": item[2],
                     "error_spans": row["error_spans"],
                     "start_time": row["start_time"],
                     "end_time": row["end_time"],
                     "login": row["login"],
                     "score": row["score"],
                     "domainID": None,
                     "documentID": None,
                     "systemID": None,
                     "sourceID": None,
                    }
            if hypothesisID not in df['hypothesisID'].values:
                df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            else:
                # replace row with content of data
                wmtitem = df.loc[df['hypothesisID'] == hypothesisID].index[0]
                df.loc[wmtitem] = data
        else:
            wmtitem = df.loc[df['hypothesisID'] == hypothesisID]
            assert len(wmtitem) == 1, f"Item {hypothesisID} not found in WMT data or found multiple times"
            wmtindex = wmtitem.index[0]

            # assert that source and hypothesis matches
            assert wmtitem['source'].iloc[0] == item[1], f"Source mismatch for {hypothesisID}"
            assert wmtitem['hypothesis'].iloc[0] == item[2], f"Translation mismatch for {hypothesisID}"

            # if annotator already annotated this item, take the newer one
            if "login" in df and df.loc[wmtindex]["login"] == row['login'] and float(df.loc[wmtindex]['end_time']) > float(row["end_time"]):
                continue

            df.at[wmtindex, "login"] = row["login"]
            df.at[wmtindex, "score"] = row["score"]
            df.at[wmtindex, "is_bad"] = row["is_bad"]
            df.at[wmtindex, "start_time"] = row["start_time"]
            df.at[wmtindex, "end_time"] = row["end_time"]

            if protocol == "LLM":
                df.at[wmtindex, "error_spans"] = item[3]
            else:
                df.at[wmtindex, "error_spans"] = row["error_spans"]

    df['error_spans'] = df['error_spans'].apply(lambda x: read_json_spans(x))

    if protocol == "LLM":
        df = df[df["is_bad"] != "BAD"].reset_index(drop=True)
        df = df.drop(columns=['login', 'start_time', 'end_time'])
        df['score'] = df["error_spans"].apply(lambda x: apply_mqm_scoring(x))
    if protocol.startswith("MQM-"):
        df['score'] = df["error_spans"].apply(lambda x: apply_mqm_scoring(x))

    # store the data
    df2 = df.copy()
    # drop BAD rows
    df2 = df2[df2["is_bad"] != "BAD"].reset_index(drop=True)
    df2["score"] = df2["score"].fillna("None")
    df2 = df2[["systemID", "score"]]

    df2.to_csv(f"campaign-ruction-rc5/en-de.{protocol}.seg.score", sep="\t", index=False, header=False)

    return df
