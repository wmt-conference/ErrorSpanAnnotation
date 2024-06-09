from itertools import combinations

from ESA.annotation_loader import AnnotationLoader
from ESA.utils import PROTOCOL_DEFINITIONS
from scipy.stats import kendalltau
import ipdb
import pandas as pd


def esa_corr_others(annotation_loader):
    methods = ["WMT-MQM", "ESA-1", "ESA-2",  "MQM-1", "WMT-DASQM"]
    df = annotation_loader.get_view(methods, only_overlap=True)

    method_scores = {}
    for method in methods:
        method_scores[f"{method}_score"] = df[f"{method}_score"].tolist()
        if "ESA" in method:
            method_scores[f"{method}_score_mqm"] = df[f"{method}_score_mqm"].tolist()

    names = PROTOCOL_DEFINITIONS.copy()
    names["ESA-1_mqm"] = {"name": f'{names["ESA-1"]["name"]}' + '$^{MQM}$'}
    names["ESA-2_mqm"] = {"name": f'{names["ESA-2"]["name"]}' + '$^{MQM}$'}

    table = {}
    for method1_i, method1 in enumerate(method_scores.keys()):
        name1 = method1.replace("_score", "")
        name1 = names[name1]["name"]
        table[name1] = {}
        for _, method2 in enumerate(list(method_scores.keys())[method1_i + 1:]):
            name2 = method2.replace("_score", "")
            name2 = names[name2]["name"]
            tau, _ = kendalltau(method_scores[method1], method_scores[method2], variant="c")
            # print(f"{method1:>20}-{method2:<20}:", f"{tau:.3f}")
            table[name1][name2] = f"{tau:.3f}"

            # normalize scores into 7 bins
            method1_binned = pd.cut(method_scores[method1], 5, labels=False)
            method2_binned = pd.cut(method_scores[method2], 5, labels=False)

            def bin_scores(scores, method):
                if "MQM" not in method:
                    thresholds = [20, 40, 60, 80, 1000]
                else:
                    thresholds = [5, 10, 15, 20, 1000]
                binned = []
                for score in scores:
                    for i, threshold in enumerate(thresholds):
                        # absolute value is to avoid handling MQM differently
                        if abs(score) <= threshold:
                            binned.append(i)
                            break
                return binned

            method1_binned = bin_scores(method_scores[method1], method1)
            method2_binned = bin_scores(method_scores[method2], method2)

            kendall, _ = kendalltau(method1_binned, method2_binned, variant="b")

            table[name1][name2] = f"{tau:.3f} ({kendall:.3f})"


    # # Kocmi: attempt for seg-level accuracy, but it doesn't attribute ties
    # df['segmentID'] = df.apply(lambda x: f"{x['documentID']}_{x['sourceID']}", axis=1)
    # systems = df['systemID'].unique()
    # for method in method_scores.keys():
    #     if "WMT-MQM" in method:
    #         continue
    #     agrees = 0
    #     total = 0
    #     for segid in df['segmentID'].unique():
    #         # for all pairs of systems
    #         for sys1, sys2 in combinations(systems, 2):
    #             subdf1 = df[(df['systemID'] == sys1) & (df['segmentID'] == segid)].iloc[0]
    #             subdf2 = df[(df['systemID'] == sys2) & (df['segmentID'] == segid)].iloc[0]
    #             diff = subdf1[f"{method}"] - subdf2[f"{method}"]
    #             wmtmqmdiff = subdf1[f"WMT-MQM_score"] - subdf2[f"WMT-MQM_score"]
    #             if wmtmqmdiff == 0:
    #                 continue
    #             total += 1
    #             if diff * wmtmqmdiff > 0:
    #                 agrees += 1
    #     print(f"{method:>10}:", f"{agrees/total:.3f}")


    tbl = pd.DataFrame(table).transpose().iloc[0]
    ipdb.set_trace()
    tbl.to_latex("PAPER_ESA/generated_plots/esa_corr_others.tex", escape=False)


if __name__ == '__main__':
    esa_corr_others(AnnotationLoader(refresh_cache=False))
