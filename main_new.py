import ipdb
import numpy as np
from absl import app
from ESA.annotation_loader import AnnotationLoader
from ESA.annotations import AppraiseAnnotations


def main(args):
    # class containing all information
    annotations = AnnotationLoader()
    # annotations.get_view(["ESA-1", "ESAAI-1", "MQM", "ESA-2", "ESAAI-2"])
    annotations.get_view(["WMT-MQM", "WMT-DASQM"])

    df = AppraiseAnnotations("GEMBA").df

    ipdb.set_trace()





if __name__ == '__main__':
    app.run(main)
