raise Exception("This code uses old loader, please refactor.")
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import numpy as np
import json
import collections
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import HuberRegressor
import pandas as pd

df = MergedAnnotations().df

data_gesa = collections.defaultdict(list)
data_esa = collections.defaultdict(list)
data_mqm = collections.defaultdict(list)
for _, row in df.iterrows():
    if type(row["LLM_error_spans"]) is not list:
        continue
    df_local = df[df.AnnotatorID_gemba == row.AnnotatorID_gemba]
    data_gesa[row.AnnotatorID_gemba].append({
        "Time": row.end_time_gemba-row.start_time_gemba,
        "Progress": np.average(df_local.end_time_gemba <= row.start_time_gemba),
        "Words": len(str(row.hypothesis).split()),
        "ErrorsIn": len(row["LLM_error_spans"]),
        "ErrorsOut": len(json.loads(row["ESAAI-1_error_spans"])),
        "Score": row.score_gemba,
        "DocumentSize": np.sum(df_local.documentID == row.documentID),
    })


    df_local = df[df.AnnotatorID_esa == row.AnnotatorID_esa]
    data_esa[row.AnnotatorID_esa].append({
        "Time": row.end_time_esa-row.start_time_esa,
        "Progress": np.average(df_local.end_time_esa <= row.start_time_esa),
        "Words": len(str(row.hypothesis).split()),
        "ErrorsOut": len(json.loads(row.span_errors_esa)),
        "Score": row.score_esa,
        "DocumentSize": np.sum(df_local.documentID == row.documentID),
    })

    df_local = df[df.AnnotatorID_mqm == row.AnnotatorID_mqm]
    data_mqm[row.AnnotatorID_mqm].append({
        "Time": row.end_time_mqm-row.start_time_mqm,
        "Progress": np.average(df_local.end_time_mqm <= row.start_time_mqm),
        "Words": len(str(row.hypothesis).split()),
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


    data_y_all = []
    data_x_all = []
    for data_local in data.values():
        data_y_all += data_local["Time"]
        data_x_all += list(pd.DataFrame.from_dict(data_local).drop(columns=["Time"]).values)
    model = HuberRegressor(epsilon=1.1, max_iter=1000)
    model.fit(data_x_all, data_y_all)
    data_y_pred = model.predict(data_x_all)
    print(f"Corr: {np.corrcoef(data_y_all, data_y_pred)[0,1]:.1%}")

    accuracies = []
    for data_local in data.values():
        data_y = data_local["Time"]
        data_x = pd.DataFrame.from_dict(data_local).drop(columns=["Time"])
        model = HuberRegressor(epsilon=1.1, max_iter=1000)
        scores = cross_val_score(model, data_x, data_y, cv=len(data_x)//2, scoring="neg_mean_absolute_error")
        accuracies.append(np.average(scores))
    print(f"MAE: {-np.average(accuracies):.2f}s")



    for feature in list(data.values())[0].keys():
        print(f"{feature:>15}: {np.average(correlations[feature]):.1%}")


print("GESA")
process_data(data_gesa)

print("ESA")
process_data(data_esa)

print("MQM")
process_data(data_mqm)