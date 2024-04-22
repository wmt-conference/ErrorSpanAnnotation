import ipdb
import numpy as np
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_MQM


def analyse_annotation_durations():
    annots = {}
    for scheme in [SCHEME_ESA, SCHEME_MQM]:
        annots[scheme] = AppraiseAnnotations(scheme)
        avg_minutes, median = annots[scheme].get_average_minutes_per_HIT()
        print(f"When filtered out long pauses: Scheme: {scheme}, Average time per HIT: {avg_minutes:.1f} minutes, Median time per HIT: {median:.1f} seconds")

    esa_df = annots[SCHEME_ESA].df
    esa_df = esa_df.drop(columns=['login', 'is_bad', 'source_lang', 'target_lang', 'span_errors', 'start_time'])

    mqm_df = annots[SCHEME_MQM].df
    mqm_df = mqm_df.drop(columns=['login', 'is_bad', 'source_lang', 'target_lang', 'span_errors', 'start_time'])
    
    # merge on ['system', 'itemID', 'documentID']
    # merged = esa_df.merge(mqm_df, on=['system', 'itemID', 'documentID'], suffixes=('_esa', '_mqm'))
    
    # median time across all annotators
    mqm_median = mqm_df['duration_seconds'].median()
    esa_median = esa_df['duration_seconds'].median()
    print(f"Median time per segment for MQM: {mqm_median:.1f} and for ESA: {esa_median:.1f}. A reduction of {100*(mqm_median-esa_median)/mqm_median:.1f}%")

    # calculate median time per annotator
    times = {"esa":[], "mqm":[]}
    for annotator in esa_df["AnnotatorID"].unique():
        times["esa"].append(esa_df[esa_df['AnnotatorID'] == annotator]['duration_seconds'].median())
    
    for annotator in mqm_df["AnnotatorID"].unique():
        times["mqm"].append(mqm_df[mqm_df['AnnotatorID'] == annotator]['duration_seconds'].median())

    # print makro average of median times
    print(f"Average median time per segment for MQM: {np.mean(times['mqm']):.1f} and for ESA: {np.mean(times['esa']):.1f}. A reduction of {100*(np.mean(times['mqm'])-np.mean(times['esa']))/np.mean(times['mqm']):.1f}%")
    