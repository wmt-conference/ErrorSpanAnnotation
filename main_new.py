import ipdb
import numpy as np
from absl import app
from ESA.annotation_loader import AnnotationLoader
from ESA.analysis.clusters_and_ranking import ClustersAndRanking


def main(args):
    # class containing all information
    annotations = AnnotationLoader(refresh_cache=False)

    # ["MQM-1", "LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "WMT-MQM", "WMT-DASQM"]
    df = annotations.get_view()

    # generate to papers
    ClustersAndRanking(annotations)


if __name__ == '__main__':
    app.run(main)
