from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=False).dropna()
import scipy.stats


def mqm_like_score(spans):
	return sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

for protocol in ["ESA", "ESAAI"]:
    corr = scipy.stats.kendalltau(df[protocol + "-1_score"], df[protocol + "-2_score"])[0]
    print(
        f"{protocol:>10} (score)   ",
        f"{corr:.3f}",
        sep=" & ", end=" \\\\\n"
	)
    scores_1 = [mqm_like_score(x) for x in df[protocol + "-1_error_spans"]]
    scores_2 = [mqm_like_score(x) for x in df[protocol + "-2_error_spans"]]
    corr = scipy.stats.kendalltau(scores_1, scores_2)[0]
    print(
        f"{protocol:>10} (MQM-like)",
        f"{corr:.3f}",
        sep=" & ", end=" \\\\\n"
	)
    