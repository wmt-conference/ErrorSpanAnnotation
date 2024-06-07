from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "MQM-1", "WMT-MQM"], only_overlap=False).dropna()
import numpy as np
import collections

data_esaai = collections.defaultdict(list)
data_esa = collections.defaultdict(list)
data_mqm = collections.defaultdict(list)

def process_first(protocol):
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
                "Words": len(str(row.hypothesis).split()),
                "ErrorsIn": len(row["LLM_error_spans"]),
                "ErrorsOut": len(row[f"{protocol}_error_spans"]),
                "Score": row[f"{protocol}_score"],
                "DocumentSize": np.sum(df_local.documentID == row.documentID),
            })
    return data_out

data_esaai = process_first("ESAAI-1") | process_first("ESAAI-2")
data_esa = process_first("ESA-1") | process_first("ESA-2")
data_mqm = process_first("MQM-1")

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
        print(f"{feature:>15}: {np.average(correlations[feature]):.2f}")


print("ESAAI")
process_data(data_esaai)

print("ESA")
process_data(data_esa)

print("MQM")
process_data(data_mqm)