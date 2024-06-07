raise Exception("Do not run. The loader does not have BAD documents at the moment.")

from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["ESA-1", "ESAAI-1", "MQM-1", "LLM"], only_overlap=False)
import re
import collections
import numpy as np

df_bad = df[df["ESAAI-1_is_bad"] == "BAD"]
df_tgt = df[df["ESAAI-1_is_bad"] == "TGT"]
data_agg = collections.defaultdict(list)

def mqm_like_score(spans):
	return 100-sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

for documentID, doc_bad in df_bad.groupby(by="documentID"):
	print(documentID)
	if re.match(r".*#duplicate\d+", documentID):
		continue
	documentID = re.sub(r"#bad\d+$", "", doc_bad.iloc[0]["documentID"])
	annotator_id = doc_bad.iloc[0]["ESAAI-1_login"]

	doc_tgt = df_tgt[(df_tgt.documentID == documentID) & (df_tgt["ESAAI-1_login"] == annotator_id)]


	doc_bad = doc_bad.sort_values(by="ESAAI-1_start_time")
	doc_tgt = doc_tgt.sort_values(by="ESAAI-1_start_time")

	# get previous and following documents
	df_user_pre = df[(df["ESAAI-1_login"] == annotator_id) & (df["ESAAI-1_start_time"] < doc_bad.iloc[0]["ESAAI-1_start_time"])].sort_values(by="ESAAI-1_start_time")
	df_user_pst = df[(df["ESAAI-1_login"] == annotator_id) & (df["ESAAI-1_start_time"] > doc_bad.iloc[-1]["ESAAI-1_start_time"])].sort_values(by="ESAAI-1_start_time")

	if len(df_user_pre) > 0 and len(df_user_pst) > 0:
		df_user_pre = df_user_pre[df_user_pre.documentID == df_user_pre.iloc[-1].documentID]
		df_user_pst = df_user_pst[df_user_pst.documentID == df_user_pst.iloc[0].documentID]

		for _, line in df_user_pre.iterrows():
			spans_gemba = {(x["start_i"], x["end_i"]) for x in line["LLM_error_spans"]}
			spans_esaai = {(x["start_i"], x["end_i"]) for x in line["ESAAI-1_error_spans"]}
			if spans_gemba:
				data_agg[("gemba_activity", "pre")].append(len(spans_gemba & spans_esaai)/len(spans_gemba))
			
		for _, line in df_user_pst.iterrows():
			spans_gemba = {(x["start_i"], x["end_i"]) for x in line["LLM_error_spans"]}
			spans_esaai = {(x["start_i"], x["end_i"]) for x in line["ESAAI-1_error_spans"]}
			if spans_gemba:
				data_agg[("gemba_activity", "pst")].append(len(spans_gemba & spans_esaai)/len(spans_gemba))
	
	assert len(doc_bad) == len(doc_tgt)

	for (_, line_bad), (_, line_tgt) in zip(doc_bad.iterrows(), doc_tgt.iterrows()):
		line_bad["span_errors_esa"] = line_bad["ESAAI-1_error_spans"]
		line_tgt["span_errors_esa"] = line_tgt["ESAAI-1_error_spans"]
		line_bad["span_errors_mqm"] = line_bad["MQM-1_error_spans"]
		line_tgt["span_errors_mqm"] = line_tgt["MQM-1_error_spans"]

		data_agg[("bad", "esa_score")].append(line_bad["ESA-1_score"])
		data_agg[("tgt", "esa_score")].append(line_tgt["ESA-1_score"])
		data_agg[("bad", "esa_spans")].append(len(line_bad["ESA-1_error_spans"]))
		data_agg[("tgt", "esa_spans")].append(len(line_tgt["ESA-1_error_spans"]))
		data_agg[("comp", "esa_spans")].append(len(line_bad["ESA-1_error_spans"])>len(line_tgt["ESA-1_error_spans"]))
		data_agg[("comp", "esa_score")].append(line_bad["ESA-1_score"] < line_tgt["ESA-1_score"])

		data_agg[("bad", "esaai_score")].append(line_bad["ESAAI-1_score"])
		data_agg[("tgt", "esaai_score")].append(line_tgt["ESAAI-1_score"])
		data_agg[("bad", "esaai_spans")].append(len(line_bad["ESAAI-1_error_spans"]))
		data_agg[("tgt", "esaai_spans")].append(len(line_tgt["ESAAI-1_error_spans"]))
		data_agg[("comp", "esaai_score")].append(line_bad["ESAAI-1_score"] < line_tgt["ESAAI-1_score"])
		data_agg[("comp", "esaai_spans")].append(len(line_bad["ESAAI-1_error_spans"])>len(line_tgt["ESAAI-1_error_spans"]))

		data_agg[("bad", "mqm_spans")].append(len(line_bad["MQM-1_error_spans"]))
		data_agg[("tgt", "mqm_spans")].append(len(line_tgt["MQM-1_error_spans"]))
		data_agg[("tgt", "mqm_score")].append(mqm_like_score(line_tgt["MQM-1_error_spans"]))
		data_agg[("bad", "mqm_score")].append(mqm_like_score(line_bad["MQM-1_error_spans"]))
		data_agg[("comp", "mqm_spans")].append(len(line_bad["MQM-1_error_spans"])>len(line_tgt["MQM-1_error_spans"]))
		data_agg[("comp", "mqm_score")].append(mqm_like_score(line_bad["MQM-1_error_spans"])<mqm_like_score(line_tgt["MQM-1_error_spans"]))


data_agg = {
	k:np.average(v) for k, v in data_agg.items()
}

prev_k = None
for k, v in data_agg.items():
	if prev_k != k[1].split("_")[0]:
		print()
		prev_k = k[1].split("_")[0]
	print(f"{'-'.join(k):>20}: {v:.3f}")