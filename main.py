from absl import app
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM
from ESA.human_scores import HumanScores
import ipdb


def main(args):
    paths = [
        ("campaign-ruction-rc5/240315rc5ESA.scores.csv", SCHEME_ESA),
        ("campaign-ruction-rc5/240315rc5MQM.scores.csv", SCHEME_MQM),
        ("campaign-ruction-rc5/240315rc5GEMBA.scores.csv", SCHEME_GEMBA)
    ]

    for path, scheme in paths:
        annotations = AppraiseAnnotations(path, scheme)
        # avg_minutes, median = annotations.get_average_minutes_per_HIT()
        # print(f"Scheme: {scheme}, Average time per HIT: {avg_minutes:.1f} minutes, Median time per HIT: {median:.1f} seconds")

        # annotations.generate_scores()



    ranks = HumanScores("en-de")
    ranks.generate_ranks()

    ipdb.set_trace()

if __name__ == '__main__':
    app.run(main)
