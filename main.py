from absl import app
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA_SEVERITY
from ESA.human_scores import HumanScores
from ESA.settings import PROJECT
from ESA.analysis_time_spans import analyse_annotation_durations
from ESA.merged_annotations import MergedAnnotations
import ipdb
import numpy as np


def main(args):
    # class containing all merged informations
    merged = MergedAnnotations(second_campaign=True)

    schemes = [SCHEME_ESA, SCHEME_MQM, SCHEME_ESA_SEVERITY]
    if PROJECT == "GEMBA":
        schemes += [SCHEME_GEMBA, SCHEME_GEMBA_SEVERITY]

    annots = {}
    for scheme in schemes:
        annots[scheme] = AppraiseAnnotations(scheme)
        # Next code is not needed to run unless the code changes
        # annots[scheme].generate_wmt_score_files()



    # GENERATE RESOURCES FOR PAPER
    ranks = HumanScores("en-de")
    ranks.generate_ranks()
    # ranks.calculate_inter_annotator_with_mqm()
    # analyse_annotation_durations()



if __name__ == '__main__':
    app.run(main)
