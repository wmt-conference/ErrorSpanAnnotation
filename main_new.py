import ipdb
import numpy as np
from absl import app
from ESA.annotation_loader import AnnotationLoader
from ESA.annotations import AppraiseAnnotations


def main(args):
    # class containing all information
    annotations = AnnotationLoader()
    annotations.get_view(["LLM", "ESA-1", "ESAAI-1", "MQM-1", "ESA-2", "ESAAI-2", "WMT-MQM", "WMT-DASQM"])

    df = AppraiseAnnotations("GEMBA").df

    ipdb.set_trace()





if __name__ == '__main__':
    app.run(main)
