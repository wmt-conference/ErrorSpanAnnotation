from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(only_overlap=True)
import numpy as np
import collections

to_average = collections.defaultdict(list)


def get_spans(spans):
	  return {(x["start_i"], x["end_i"]) for x in spans}

for _, row in df.iterrows():
	spans_gemba = row["LLM_error_spans"]
	spans_gesa = row["ESAAI-1_error_spans"]
	spans_removed = [
		s1 for s1 in spans_gemba
		if not any([s2["start_i"] == s1["start_i"] and s2["end_i"] == s1["end_i"] for s2 in spans_gesa])
	]
	spans_added = [
		s2 for s2 in spans_gesa
		if not any([s2["start_i"] == s1["start_i"] and s2["end_i"] == s1["end_i"] for s1 in spans_gemba])
	]

	spans_severity_inc = [
		(s1, s2)
		for s1 in spans_gemba
		for s2 in spans_gesa
		if (
			s1["start_i"] == s2["start_i"] and s1["end_i"] == s2["end_i"] and
			s1["severity"] == "minor" and s2["severity"] == "major"
		)
		]
	spans_severity_dec = [
		(s1, s2)
		for s1 in spans_gemba
		for s2 in spans_gesa
		if (
			s1["start_i"] == s2["start_i"] and s1["end_i"] == s2["end_i"] and
			s2["severity"] == "minor" and s1["severity"] == "major"
		)
		]
	
	to_average["spans_severity_inc"].append(len(spans_severity_inc))
	to_average["spans_severity_dec"].append(len(spans_severity_dec))
	
	def span_close(s1, s2, threshold=10):
		if s1["start_i"] == "missing" and s2["start_i"] == "missing":
			return True
		if (s1["start_i"] == "missing") != (s2["start_i"] == "missing"):
			return True
		s1["start_i"] = int(s1["start_i"])
		s1["end_i"] = int(s1["end_i"])
		s2["start_i"] = int(s2["start_i"])
		s2["end_i"] = int(s2["end_i"])
		return abs(s1["start_i"]-s2["start_i"]) <= threshold and abs(s1["end_i"]-s2["end_i"]) <= threshold

	def span_len(s1):
		if s1["start_i"] == "missing":
			return 0
		else:
			return int(s1["end_i"])-int(s1["start_i"])

	spans_moved_t20 = [
		(s1, s2)
		for s1 in spans_removed
		for s2 in spans_added
		if span_close(s1, s2, threshold=20)
	]
	spans_moved_t10 = [
		(s1, s2)
		for s1 in spans_removed
		for s2 in spans_added
		if span_close(s1, s2, threshold=10)
	]
	spans_moved_t5 = [
		(s1, s2)
		for s1 in spans_removed
		for s2 in spans_added
		if span_close(s1, s2, threshold=5)
	]

	to_average["spans_moved_t20"].append(len(spans_moved_t20))
	to_average["spans_moved_t10"].append(len(spans_moved_t10))
	to_average["spans_moved_t5"].append(len(spans_moved_t5))
	spans_moved_inc = [
		(s1, s2) for s1, s2 in spans_moved_t20
		if span_len(s1) < span_len(s2)
	]
	spans_moved_dec = [
		(s1, s2) for s1, s2 in spans_moved_t20
		if span_len(s1) > span_len(s2)
	]
	to_average["spans_moved_inc"].append(len(spans_moved_inc))
	to_average["spans_moved_dec"].append(len(spans_moved_dec))

	to_average["gemba_span_len_no_norm"] += [
		span_len(s1) for s1 in spans_gemba
	]
	to_average["gesa_span_len_no_norm"] += [
		span_len(s1) for s1 in spans_gesa
	]
	to_average["normalizer"].append(len(spans_added))
	

	to_average["severity_diff_no_norm"].append(
		len([s1 for s1 in spans_added if s1["severity"] == "major"]) -
        len([s1 for s1 in spans_added if s1["severity"] == "minor"])
    )

	# to find examples
	if spans_moved_inc and len(spans_gesa) <= 3 and len(row.hypothesis) <= 100:
		print(row.source)
		print(row.hypothesis)
		print(spans_gesa)
		print()
	

normalization = np.average(to_average.pop("normalizer"))

for k, v in to_average.items():
	if "no_norm" in k:
		print(f"{k:>25}: {np.average(v):.1f}")
	else:
		print(f"{k:>25}: {np.average(v)/normalization:.2%}")