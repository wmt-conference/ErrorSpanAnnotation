import ipdb
import pandas as pd


class HumanScores:
    def __init__(self, language_pair):
        self.language_pair = language_pair
        self.resources = None

        # load protocol
        scores = {}
        systems = []
        for protocol in ["wmt-mqm", "wmt-dasqm", "esa", "mqm", "gemba"]:
            if protocol == "wmt-mqm":
                path = f"mt-metrics-eval-v2/wmt23/human-scores/{language_pair}.mqm.seg.score"
            elif protocol == "wmt-dasqm":
                path = f"mt-metrics-eval-v2/wmt23/human-scores/{language_pair}.da-sqm.seg.score"
            elif protocol == "esa":
                path = f"campaign-ruction-rc5/{language_pair}.ESA.seg.score"
            elif protocol == "mqm":
                path = f"campaign-ruction-rc5/{language_pair}.MQM.seg.score"
            elif protocol == "gemba":
                path = f"campaign-ruction-rc5/{language_pair}.GEMBA.seg.score"

            scores["system"] = pd.read_csv(path, sep="\t", header=None, names=["system", "score"])['system']
            scores[protocol] = pd.read_csv(path, sep="\t", header=None, names=["system", "score"])['score']

        # merge scores
        self.resources = pd.DataFrame(scores)

    def generate_ranks(self):
        df = self.resources
        # replace in all columns string "None" with NaN
        df = df.replace("None", float("nan"))
        df = df.dropna()

        # convert all scores to float
        for col in df.columns:
            if col != "system":
                df[col] = df[col].astype(float)
        # group by system
        df = df.groupby("system").mean()
        df.groupby("system").mean().to_excel("delme2.xlsx")
        ipdb.set_trace()
