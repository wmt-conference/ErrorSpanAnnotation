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


    tbl = pd.DataFrame(table).transpose()
    tbl.iloc[0].to_latex("PAPER_ESA/generated_plots/esa_corr_others.tex", escape=False)


if __name__ == '__main__':
    esa_corr_others(AnnotationLoader(refresh_cache=False))
