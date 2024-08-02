from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=False).dropna()
import scipy.stats


def mqm_like_score(spans):
	return sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

print("Inter annotator agreement")

for protocol in ["ESA", "ESAAI"]:
    corr = scipy.stats.spearmanr(df[protocol + "-1_score"], df[protocol + "-2_score"])[0]
    print(
        f"{protocol:>10} (score)   ",
        f"{corr:.3f}",
        sep=" & ", end=" \\\\\n"
	)
    scores_1 = [mqm_like_score(x) for x in df[protocol + "-1_error_spans"]]
    scores_2 = [mqm_like_score(x) for x in df[protocol + "-2_error_spans"]]
    corr = scipy.stats.spearmanr(scores_1, scores_2)[0]
    print(
        f"{protocol:>10} (MQM-like)",
        f"{corr:.3f}",
        sep=" & ", end=" \\\\\n"
	)
    

print("Intra annotator agreement")
df = AnnotationLoader(refresh_cache=False).get_view(["ESA-1", "ESAAI-1", "ESA-IAA", "ESAAI-IAA"], only_overlap=True).dropna()

for protocol in ["ESA", "ESAAI"]:
    corr = scipy.stats.spearmanr(df[protocol + "-1_score"], df[protocol + "-IAA_score"])[0]
    print(
        f"{protocol:>10} (score)   ",
        f"{corr:.3f}",
        sep=" & ", end=" \\\\\n"
	)
    scores_1 = [mqm_like_score(x) for x in df[protocol + "-1_error_spans"]]
    scores_2 = [mqm_like_score(x) for x in df[protocol + "-IAA_error_spans"]]
    corr = scipy.stats.spearmanr(scores_1, scores_2)[0]
    print(
        f"{protocol:>10} (MQM-like)",
        f"{corr:.3f}",
        sep=" & ", end=" \\\\\n"
	)