from ESA.annotation_loader import AnnotationLoader
from ESA.utils import PROTOCOL_DEFINITIONS
from scipy.stats import kendalltau
import ipdb
import pandas as pd

methods = ["WMT-MQM", "ESA-1", "ESA-2",  "MQM-1", "WMT-DASQM"]
df = AnnotationLoader(refresh_cache=False).get_view(methods, only_overlap=True)

methods += ["ESA-1_score_mqm"]
methods += ["ESA-2_score_mqm"]
method_scores = {}
for method in methods:
    if method == "ESA-1_score_mqm" or method == "ESA-2_score_mqm":
        method_scores[method] = df[f"{method}"].tolist()
    else:
        method_scores[method] = df[f"{method}_score"].tolist()

table = {}
for method1_i, method1 in enumerate(methods):
    name1 = method1
    table[name1] = {}
    for _, method2 in enumerate(methods[method1_i + 1:]):
        name2 = method2
        if method1.startswith("ESA") and method2.startswith("ESA"):
            tau, _ = kendalltau(method_scores[method1], method_scores[method2], variant="b")
        else:
            tau, _ = kendalltau(method_scores[method1], method_scores[method2], variant="c")
        print(f"{method1:>20}-{method2:<20}:", f"{tau:.3f}")
        table[name1][name2] = tau

df = pd.DataFrame(table)
ipdb.set_trace()
