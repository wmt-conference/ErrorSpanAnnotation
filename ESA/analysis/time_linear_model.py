import ESA.settings
ESA.settings.PROJECT = "esa"
from ESA.merged_annotations import MergedAnnotations
import numpy as np
import json
import statsmodels.formula.api as smf
import pandas as pd

df = MergedAnnotations().df


data = []
for _, row in df.iterrows():
    df_local = df[df.AnnotatorID_gemba == row.AnnotatorID_gemba]
    data.append({
        "Time": row.end_time_gemba-row.start_time_gemba,
        "Annotator": row.AnnotatorID_gemba,
        "Progress": 100*np.average(df_local.end_time_gemba <= row.start_time_gemba),
        "Words": len(str(row.translation_seg).split()),
        "ErrorsOut": len(json.loads(row.span_errors_gemba)),
        "DocumentSize": np.sum(df_local.documentID == row.documentID),
    })

# transpose
data = {k:[x[k] for x in data] for k in data[0].keys
        ()}
data = pd.DataFrame.from_dict(data)

model = smf.mixedlm("Time ~ Progress + Words + ErrorsOut + DocumentSize", data, groups=data["Annotator"])
model_fit = model.fit()
print(model_fit.summary())

import collections


data_gesa = collections.defaultdict(list)
data_esa = collections.defaultdict(list)
data_mqm = collections.defaultdict(list)
for _, row in df.iterrows():
    if type(row.gemba_mqm_span_errors_gemba) is not list:
        continue
    df_local = df[df.AnnotatorID_gemba == row.AnnotatorID_gemba]
    data_gesa[row.AnnotatorID_gemba].append({
        "Time": row.end_time_gemba-row.start_time_gemba,
        "Progress": np.average(df_local.end_time_gemba <= row.start_time_gemba),
        "Words": len(str(row.translation_seg).split()),
        "ErrorsIn": len(row.gemba_mqm_span_errors_gemba),
        "ErrorsOut": len(json.loads(row.span_errors_gemba)),
        "Score": row.score_gemba,
        "DocumentSize": np.sum(df_local.documentID == row.documentID),
    })


    df_local = df[df.AnnotatorID_esa == row.AnnotatorID_esa]
    data_esa[row.AnnotatorID_esa].append({
        "Time": row.end_time_esa-row.start_time_esa,
        "Progress": np.average(df_local.end_time_esa <= row.start_time_esa),
        "Words": len(str(row.translation_seg).split()),
        "ErrorsOut": len(json.loads(row.span_errors_esa)),
        "Score": row.score_esa,
        "DocumentSize": np.sum(df_local.documentID == row.documentID),
    })

    df_local = df[df.AnnotatorID_mqm == row.AnnotatorID_mqm]
    data_mqm[row.AnnotatorID_mqm].append({
        "Time": row.end_time_mqm-row.start_time_mqm,
        "Progress": np.average(df_local.end_time_mqm <= row.start_time_mqm),
        "Words": len(str(row.translation_seg).split()),
        "ErrorsOut": len(json.loads(row.span_errors_mqm)),
        "Score": row.score_mqm,
        "DocumentSize": np.sum(df_local.documentID == row.documentID),
    })

def process_data(data):
    # transpose
    data = {
        annotator:
        {feature:[x[feature] for x in data_local] for feature in data_local[0].keys()}
        for annotator, data_local in data.items()
    }

    correlations = {}
    for feature in list(data.values())[0].keys():
        correlations[feature] = [
            np.corrcoef(data_local[feature], data_local["Time"])[0,1]
            for data_local in data.values()
        ]

    for feature in list(data.values())[0].keys():
        print(f"{feature:>15}: {np.average(correlations[feature]):.1%}")


print("GESA")
process_data(data_gesa)

print("ESA")
process_data(data_esa)

print("MQM")
process_data(data_mqm)