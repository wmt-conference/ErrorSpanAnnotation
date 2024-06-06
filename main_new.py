import ipdb
import numpy as np
from absl import app
from ESA.annotation_loader import AnnotationLoader


def main(args):
    # class containing all information
    annotations = AnnotationLoader(refresh_cache=False)

    df = annotations.get_view()


if __name__ == '__main__':
    app.run(main)
