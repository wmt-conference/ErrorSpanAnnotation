from ESA.annotation_loader import AnnotationLoader
methods = ["ESA-1", "MQM-1", "WMT-MQM", "WMT-DASQM"]
df = AnnotationLoader(refresh_cache=False).get_view(methods, only_overlap=True)
import scipy.stats


methods += ["ESA-1_score_mqm"]
method_scores = {}
for method in methods:
	if method == "ESA-1_score_mqm":
		method_scores[method] =  df[f"{method}"].tolist()
	else:
		method_scores[method] =  df[f"{method}_score"].tolist()
		

for method1_i, method1 in enumerate(methods):
    for _, method2 in enumerate(methods[method1_i+1:]):
        print(
			f"{method1:>20}-{method2:<20}:",
			f"{scipy.stats.kendalltau(method_scores[method1], method_scores[method2])[0]:.3f}"
        )