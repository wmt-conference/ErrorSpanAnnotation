import ipdb
import pandas as pd


class HumanScores:
    def __init__(self, protocol, language_pair):
        self.protocol = protocol
        self.language_pair = language_pair
        self.resources = None

        # load protocol
        if self.protocol == "wmt-mqm":
            path = f"mt-metrics-eval-v2/wmt23/human-scores/{language_pair}.mqm.seg.score"
        elif self.protocol == "wmt-dasqm":
            path = f"mt-metrics-eval-v2/wmt23/human-scores/{language_pair}.da-sqm.seg.score"
        elif self.protocol == "esa":
            path = f"campaign-ruction-rc5/{language_pair}.esa.seg.score"
        elif self.protocol == "mqm":
            path = f"campaign-ruction-rc5/{language_pair}.mqm.seg.score"
        elif self.protocol == "gemba":
            path = f"campaign-ruction-rc5/{language_pair}.gemba.seg.score"

        pd.read_csv(path, sep="\t")


        ipdb.set_trace()