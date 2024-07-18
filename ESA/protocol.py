import ipdb
import pandas as pd
from ESA.utils import load_raw_appraise_campaign, load_raw_wmt, PROTOCOL_DEFINITIONS


class Protocol:
    def __init__(self, protocol):
        self.protocol = protocol
        assert protocol in PROTOCOL_DEFINITIONS.keys(), f"Protocol {protocol} not supported. Allowed protocols are {PROTOCOL_DEFINITIONS.keys()}."

        if PROTOCOL_DEFINITIONS[protocol]["framework"] == "appraise":
            self.df = load_raw_appraise_campaign(protocol)
        elif PROTOCOL_DEFINITIONS[protocol]["framework"] == "wmt":
            self.df = load_raw_wmt(protocol)
        else:
            raise NotImplementedError(f"Protocol {protocol} not implemented yet.")

        self.df["hypID"] = self.df['hypothesisID']
        self.df.set_index('hypID', inplace=True)

        if "start_time" in self.df.columns:
            self.df["start_time"] = self.df["start_time"].astype(float)
            self.df["end_time"] = self.df["end_time"].astype(float)

        self._append_human_ids()
        self._estimate_annotation_duration()

    def _append_human_ids(self):
        if "login" in self.df.columns:
            annotator_mapping = pd.read_csv("data/campaignruction-rc5/Annotators_mapping.csv")
            annotator_mapping = annotator_mapping[["AnnotatorID", "login"]]
            annotator_mapping["AnnotatorID"] = "Human_" + annotator_mapping["AnnotatorID"].astype(str)

            mapping = annotator_mapping.set_index("login").to_dict()["AnnotatorID"]
            self.df['AnnotatorID'] = self.df['login'].apply(lambda x: mapping.get(x, x))

    def _estimate_annotation_duration(self):
        if "login" in self.df.columns:
            self.df["duration_seconds"] = 0
            for login in self.df.login.dropna().unique():
                subdf = self.df[self.df['login'] == login]
                subdf = subdf.sort_values("start_time")
                previous_timestamp = subdf.iloc[0]["start_time"]
                for i in range(1, len(subdf)):
                    index = subdf.index[i]
                    diff = self.df.loc[index]["start_time"] - previous_timestamp

                    previous_timestamp = self.df.loc[index]["start_time"]
                    self.df.at[index, "duration_seconds"] = diff