from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "MQM-1", "WMT-MQM"], only_overlap=False).dropna()
import scipy.stats

def mqm_like_score(spans):
	return -sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

method_scores = {}
for method in ["ESA-1_score", "ESAAI-1_score", "MQM-1_score", "WMT-MQM_score", "LLM"]:
	if method == "LLM":
		method_scores[method] = [mqm_like_score(x) for x in df["LLM_error_spans"]]
	else:
		method_scores[method] =  df[method].tolist()
		

methods = list(method_scores.keys())
for method1_i, method1 in enumerate(methods):
    for _, method2 in enumerate(methods[method1_i+1:]):
        print(
			f"{method1:>20}-{method2:<20}:",
			f"{scipy.stats.kendalltau(method_scores[method1], method_scores[method2])[0]:.3f}"
        )