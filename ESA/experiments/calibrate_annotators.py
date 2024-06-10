import os
import ipdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.stats import ranksums, mannwhitneyu, wilcoxon
from itertools import combinations
from ESA.utils import PROTOCOL_DEFINITIONS
from ESA.annotation_loader import AnnotationLoader
from sklearn.linear_model import LinearRegression, HuberRegressor


def calibrate_annotators(annotations_loader):
    df = annotations_loader.get_view(["ESA-1", "ESA-2", "WMT-MQM"], only_overlap=True)

    protocol = "ESA-1"
    df[f'{protocol}_minor_count'] = df[f'{protocol}_error_spans'].apply(lambda x: len([y for y in x if y['severity'] == 'minor']))
    df[f'{protocol}_major_count'] = df[f'{protocol}_error_spans'].apply(lambda x: len([y for y in x if y['severity'] == 'major']))

    annotators = df[f'{protocol}_AnnotatorID'].unique()
    # define plot with subplots for each annotator
    fig, ax = plt.subplots(2, int(len(annotators)/2), figsize=(20, 5))
    ax = ax.flatten()

    for index, annotatorID in enumerate(annotators):
        subdf = df[df[f'{protocol}_AnnotatorID'] == annotatorID]

        model = LinearRegression()
        model.fit(subdf[[f'{protocol}_minor_count', f'{protocol}_major_count']], subdf[f'{protocol}_score'])
        a, b = model.coef_
        print(f"Minor weight: 1; Major weight: {b/a:.1f}", annotatorID)

        # plot histogram of annotations
        ax[index].hist(subdf[f'{protocol}_score'], bins=20)
        # make title for each annotator
        ax[index].set_title(annotatorID)

    plt.show()
    ipdb.set_trace()


if __name__ == '__main__':
    calibrate_annotators(AnnotationLoader(refresh_cache=False))
