from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["ESA-1"], only_overlap=False).dropna()
import numpy as np
import collections
import sklearn.linear_model

def process(protocol):
    data_out = collections.defaultdict(list)
    for annotatorID, df_local in df.groupby(f"{protocol}_AnnotatorID"):
        time_median = np.median(df_local[f"{protocol}_duration_seconds"])
        for _, row in df_local.iterrows():
            if row[f"{protocol}_duration_seconds"] > 60*5:
                time = time_median
            else:
                time = row[f"{protocol}_duration_seconds"]
            
            data_out[annotatorID].append({
                "Time": time,
                "Progress": np.average(df_local[f"{protocol}_start_time"] <= row[f"{protocol}_start_time"]),
                "Words": len(str(row.source).split()),
                "Source": str(row.source),
                "Hypothesis": str(row.hypothesis),
                "ErrorsOut": len(row[f"{protocol}_error_spans"]),
                "Score": row[f"{protocol}_score"],
                "DocumentSize": np.sum(df_local.documentID == row.documentID),
                "Annotator": annotatorID,
            })

            # if len(str(row.source).split()) > 20 and time > 200:
            #     print("SRC", str(row.source))
            #     print("TGT", str(row.hypothesis))
            #     print("Time", time)
            #     print()

    for annotatorID, l in data_out.items():
        mean = np.average([x["Time"] for x in l])
        for line in l:
            line["AnnotatorMean"] = mean

    data_x = [x["Time"] for l in data_out.values() for x in l]
    data_y = [[x["Words"]] for l in data_out.values() for x in l]
    model = sklearn.linear_model.LinearRegression()

    model.fit(data_y, data_x)
    data_y_pred = model.predict(data_y)

    print("Coefs", model.coef_)
    print("Intercept", model.intercept_)

    print("Corr", np.corrcoef(data_x, data_y_pred)[0,1])

process("ESA-1")



