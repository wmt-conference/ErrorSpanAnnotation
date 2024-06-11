raise Exception("This code uses old loader, please refactor.")
from absl import app
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA_SEVERITY, analyse_annotation_durations

from ESA.merged_annotations import MergedAnnotations
import ipdb
import numpy as np


def main(args):
    # class containing all merged informations
    merged = MergedAnnotations(second_campaign=True)

    schemes = [SCHEME_ESA, SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA, SCHEME_GEMBA_SEVERITY]

    annots = {}
    for scheme in schemes:
        annots[scheme] = AppraiseAnnotations(scheme)
        # annots[scheme].get_average_minutes_per_HIT()
        # Next code is not needed to run unless the code changes
        # annots[scheme].generate_wmt_score_files()



    # GENERATE RESOURCES FOR PAPER
    # analyse_annotation_durations()



if __name__ == '__main__':
    app.run(main)
