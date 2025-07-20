import csv
import numpy as np


data_esaai = list(csv.DictReader(open('data/survey_esaai.csv', 'r')))
data_esa = list(csv.DictReader(open('data/survey_esa.csv', 'r')))

MAPPING = {
    "Strongly agree": 5, "Agree": 4, "Neutral": 3, "Disagree": 2, "Strongly disagree": 1,
    "-2 (negative)": 1, "-1": 2, "0": 3, "+1": 4, "+2 (positive)": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5
}

def rename_key(k):
    return (
        k
        .replace("Please specify how much you agree or disagree with the following statements.  ", "")
        .replace("This evaluation campaign featured the Error Span Annotation evaluation method with Scalar Quality Metrics. What do you think about this method? It was...  ", "In comparison to DA+SQM: ")
        .replace("[", "").replace("]", "")
    )

def process_survey(data):
    keys = data[0].keys()
    likert_keys = [
        k for k in keys if data[0][k] in MAPPING]
    
    return {
        f"{rename_key(k):>70}": f"{np.average([MAPPING[d[k]] for d in data]):.1f}"
        for k in likert_keys
    }
    

data_esaai = process_survey(data_esaai)
data_esa = process_survey(data_esa)

print("ESAAI", "ESA")
for k in data_esaai.keys():
    print(
        k,
        data_esaai[k],
        data_esa[k] if k in data_esa else "",
        sep=" & ", end=" \\\\\n"
    )