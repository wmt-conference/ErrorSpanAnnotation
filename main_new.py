import ipdb
import pandas as pd
import numpy as np
from absl import app
from collections import defaultdict
from ESA.annotation_loader import AnnotationLoader
from ESA.experiments.clusters_and_ranking import ClustersAndRanking
from ESA.experiments.intra_annotator_agreement import IntraAnnotatorAgreement
from ESA.experiments.overview_segment_count_esa import overview_segment_count_esa
from ESA.utils import PROTOCOL_DEFINITIONS


def main(args):
    # class containing all information
    annotations = AnnotationLoader(refresh_cache=False)

    # ["MQM-1", "LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "WMT-MQM", "WMT-DASQM"]
    df = annotations.get_view(only_overlap=True)

    # df = df.dropna()
    # for protocol in ["ESA"]:
    #     subdf = df[[f'{protocol}-1_score', f'{protocol}-IAA_score']]
    #     pearson = subdf.corr().iloc[0, 1]
    #     print(f"{protocol} pearson: {pearson:.3f} on {len(subdf)} samples")
    #
    #     subdf = df[[f'{protocol}-1_score_mqm', f'{protocol}-IAA_score_mqm']]
    #     # convert to float
    #     subdf = subdf.applymap(lambda x: float(x))
    #     pearson = subdf.corr().iloc[0, 1]
    #     print(f"MQM {protocol} pearson: {pearson:.3f} on {len(subdf)} samples")
    #
    #
    # subdf = df[[f'MQM-1_score', f'WMT-MQM_score']]
    # pearson = subdf.corr().iloc[0, 1]
    # print(f"MQM pearson: {pearson:.3f} on {len(subdf)} samples")
    #
    #
    # # df = annotations.get_view(only_overlap=False)
    # # df2 = df[['systemID', 'WMT-MQM_error_spans', 'WMT-DASQM_score']].dropna()
    # # df2 = df2[df2['systemID'].isin(['refA', 'GPT4-5shot'])]
    # #
    # # error_categories = defaultdict(int)
    # # for index, row in df2.iterrows():
    # #     for error in row['WMT-MQM_error_spans']:
    # #         error_categories[f"{row['systemID']}_{error['severity']}_{error['category']}"] += 1
    #
    # # df = df[['WMT-MQM_error_spans', 'WMT-DASQM_score']].dropna()
    # # errors = []
    # # for index, row in df.iterrows():
    # #     if len(row['WMT-MQM_error_spans']) > 1:
    # #         continue
    # #     for error in row['WMT-MQM_error_spans']:
    # #         errors.append([f"{error['severity']}_{error['category']}", row['WMT-DASQM_score']])
    # #
    # # errs = pd.DataFrame(errors, columns=['error', 'score'])
    # # er = errs.groupby('error').agg(['mean', 'count']).reset_index()
    #
    #
    # ipdb.set_trace()


    # generate to papers
    ClustersAndRanking(annotations)
    IntraAnnotatorAgreement(annotations)
    overview_segment_count_esa(annotations)


if __name__ == '__main__':
    app.run(main)
