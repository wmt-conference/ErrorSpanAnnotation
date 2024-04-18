from absl import app
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM
from ESA.human_scores import HumanScores
import ipdb




def main(args):
    schemes = [
        (SCHEME_ESA),
        (SCHEME_MQM),
        (SCHEME_GEMBA)
    ]

    for scheme in schemes:
        annotations = AppraiseAnnotations(scheme)
        # avg_minutes, median = annotations.get_average_minutes_per_HIT()
        # print(f"Scheme: {scheme}, Average time per HIT: {avg_minutes:.1f} minutes, Median time per HIT: {median:.1f} seconds")

        # Next code is not needed to run unless the code changes
        # annotations.generate_scores(True)
        # annotations.generate_scores(True) # this also generates ESA and GEMBA with severity


    # GENERATE RESOURCES FOR PAPER

    ranks = HumanScores("en-de")
    ranks.generate_ranks()


if __name__ == '__main__':
    app.run(main)
