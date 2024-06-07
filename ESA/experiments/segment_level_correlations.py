import ipdb
import pandas as pd
import numpy as np
from absl import app
from ESA.annotation_loader import AnnotationLoader
from ESA.experiments.clusters_and_ranking import ClustersAndRanking
from ESA.utils import PROTOCOL_DEFINITIONS


def main(args):
    # class containing all information
    annotations = AnnotationLoader(refresh_cache=False)

    # ["MQM-1", "LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "WMT-MQM", "WMT-DASQM"]
    df = annotations.get_view(only_overlap=True)

    df['segID'] = df.apply(lambda x: f"{x['sourceID']}#{x['documentID']}", axis=1)
    corrs = {}
    kendalls = {}

    avg_spearman = {}
    from itertools import combinations
    from scipy.stats import spearmanr
    for protocol in PROTOCOL_DEFINITIONS.keys():
        subdf = df[["WMT-MQM_score", f"{protocol}_score"]]
        corrs[protocol] = {
            "pearson": subdf.corr(method='pearson').iloc[0, 1],
            "spearman": subdf.corr(method='spearman').iloc[0, 1],
            "kendall": subdf.corr(method='kendall').iloc[0, 1]
        }

        # create all pairs of systems
        concordants = 0
        discordants = 0
        systems = df['systemID'].unique()
        segments = df['segID'].unique()
        for sys1, sys2 in combinations(systems, 2):
            # for each segID calculate difference
            for segID in segments:
                subdf = df[df['segID'] == segID]
                score1 = subdf[subdf['systemID'] == sys1][f"{protocol}_score"].values[0]
                score2 = subdf[subdf['systemID'] == sys2][f"{protocol}_score"].values[0]
                diff = score1 - score2

                mqm1 = subdf[subdf['systemID'] == sys1]['WMT-MQM_score'].values[0]
                mqm2 = subdf[subdf['systemID'] == sys2]['WMT-MQM_score'].values[0]
                diff_mqm = mqm1 - mqm2
                # if diff_mqm == 0:
                #     continue

                if diff * diff_mqm > 0:
                    concordants += 1
                else:
                    discordants += 1

        kendalls[protocol] = (concordants - discordants) / (concordants + discordants)

        spearmans = []
        for segID in segments:
            subdf = df[df['segID'] == segID]

            scores = subdf[f"{protocol}_score"].values
            mqm_scores = subdf['WMT-MQM_score'].values
            # check that sum is not 0
            # if int(np.sum(mqm_scores)) == 0 or int(np.sum(scores)) == 0:
            #     continue
            # print(scores, mqm_scores)
            # coef = np.corrcoef(mqm_scores, scores)[0, 1]
            coef, _ = spearmanr(mqm_scores, scores)
            if np.isnan(coef):
                continue
            spearmans.append(coef)

        avg_spearman[protocol] = np.mean(spearmans)


    print(pd.DataFrame([avg_spearman]).transpose().sort_values(by=0))
    print(pd.DataFrame([kendalls]).transpose().sort_values(by=0))
    ipdb.set_trace()


    # TODO next part is attempt for documentlevel correlation
    # avg_spearman = {}
    # from itertools import combinations
    # from scipy.stats import spearmanr
    # for protocol in PROTOCOL_DEFINITIONS.keys():
    #     # create all pairs of systems
    #     concordants = 0
    #     discordants = 0
    #     systems = df['systemID'].unique()
    #     segments = df['segID'].unique()
    #     documents = df['domainID'].unique()
    #     for sys1, sys2 in combinations(systems, 2):
    #         # for each segID calculate difference
    #         for docID in documents:
    #             subdf = df[df['domainID'] == docID]
    #
    #             score1 = subdf[subdf['systemID'] == sys1][f"{protocol}_score"].mean()
    #             score2 = subdf[subdf['systemID'] == sys2][f"{protocol}_score"].mean()
    #             diff = score1 - score2
    #
    #             mqm1 = subdf[subdf['systemID'] == sys1]['WMT-MQM_score'].mean()
    #             mqm2 = subdf[subdf['systemID'] == sys2]['WMT-MQM_score'].mean()
    #             diff_mqm = mqm1 - mqm2
    #             # if diff_mqm == 0:
    #             #     continue
    #
    #             if diff * diff_mqm > 0:
    #                 concordants += 1
    #             else:
    #                 discordants += 1
    #
    #     kendalls[protocol] = (concordants - discordants) / (concordants + discordants)
    #
    # # print(pd.DataFrame([avg_spearman]).transpose().sort_values(by=0))
    # print(pd.DataFrame([kendalls]).transpose().sort_values(by=0))
    # ipdb.set_trace()

if __name__ == '__main__':
    app.run(main)
