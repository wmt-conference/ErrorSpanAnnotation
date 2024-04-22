from absl import app
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA_SEVERITY
from ESA.human_scores import HumanScores
import ipdb




def main(args):
    schemes = [SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA_SEVERITY]

    annots = {}
    for scheme in schemes:
        annots[scheme] = AppraiseAnnotations(scheme)
        avg_minutes, median = annots[scheme].get_average_minutes_per_HIT()
        print(f"Scheme: {scheme}, Average time per HIT: {avg_minutes:.1f} minutes, Median time per HIT: {median:.1f} seconds")

        avg_minutes, median = annots[scheme].get_average_minutes_per_HIT(unfiltered=True)
        # Next code is not needed to run unless the code changes
        annots[scheme].generate_wmt_score_files()
               


    # GENERATE RESOURCES FOR PAPER

    ranks = HumanScores("en-de")
    ranks.generate_ranks()


if __name__ == '__main__':
    app.run(main)
