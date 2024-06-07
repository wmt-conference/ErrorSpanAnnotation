from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["MQM-1", "LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=False)
import re
import collections
import numpy as np
import os

df_bad = df[df["ESAAI-1_is_bad"] == "BAD"]
df_tgt = df[df["ESAAI-1_is_bad"] == "TGT"]
data_agg = collections.defaultdict(list)

def mqm_like_score(spans):
	return 100-sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

def get_perturbation_index(hyp_bad, hyp_tgt):
	start_i = len(os.path.commonprefix([hyp_bad, hyp_tgt]))
	end_len = len(os.path.commonprefix([hyp_bad[::-1], hyp_tgt[::-1]]))
	return (start_i, len(hyp_bad)-end_len)

def did_mark_perturbation(line_bad, line_tgt, protocol):
	start_i, end_i = get_perturbation_index(line_bad["hypothesis"], line_tgt["hypothesis"])
	return any([
		(start_i <= x["end_i"] and end_i >= x["start_i"])
		for x in line_bad[protocol + "_error_spans"]
		if x["start_i"] != "missing" and x["end_i"] != "missing"
	])

for hypothesisID, doc_bad in df_bad.groupby("hypothesisID"):
	if re.match(r".*#duplicate\d+", hypothesisID):
		continue
	hypothesisID = re.sub(r"#bad\d+$", "", doc_bad.iloc[0]["hypothesisID"])
	login_iud = doc_bad.iloc[0]["ESAAI-1_login"]

	doc_tgt = df_tgt[(df_tgt.hypothesisID == hypothesisID) & (df_tgt["ESAAI-1_login"] == login_iud)]

	doc_bad = doc_bad.sort_values(by="ESAAI-1_start_time")
	doc_tgt = doc_tgt.sort_values(by="ESAAI-1_start_time")

	assert len(doc_bad) == 1
	assert len(doc_tgt) == 1

	# get previous and following documents
	df_user_pre = df[(df["ESAAI-1_login"] == login_iud) & (df["ESAAI-1_start_time"] < doc_bad.iloc[0]["ESAAI-1_start_time"])].sort_values(by="ESAAI-1_start_time")
	df_user_pst = df[(df["ESAAI-1_login"] == login_iud) & (df["ESAAI-1_start_time"] > doc_bad.iloc[-1]["ESAAI-1_start_time"])].sort_values(by="ESAAI-1_start_time")

	# check collaboration before and after
	if len(df_user_pre) > 0 and len(df_user_pst) > 0:
		df_user_pre = df_user_pre[df_user_pre.hypothesisID == df_user_pre.iloc[-1].hypothesisID]
		df_user_pst = df_user_pst[df_user_pst.hypothesisID == df_user_pst.iloc[0].hypothesisID]

		assert len(df_user_pre) == 1
		assert len(df_user_pst) == 1

		df_user_pre = df_user_pre.iloc[0]
		df_user_pst = df_user_pst.iloc[0]

		if type(df_user_pre["LLM_error_spans"]) is float:
			continue
		if type(df_user_pst["LLM_error_spans"]) is float:
			continue

		spans_gemba = {(x["start_i"], x["end_i"]) for x in df_user_pre["LLM_error_spans"]}
		spans_esaai = {(x["start_i"], x["end_i"]) for x in df_user_pre["ESAAI-1_error_spans"]}
		if spans_gemba:
			data_agg[("gemba_agree", "pre")].append(len(spans_gemba & spans_esaai)/len(spans_gemba))
		else:
			data_agg[("gemba_agree", "pre")].append(1)
		
		spans_gemba = {(x["start_i"], x["end_i"]) for x in df_user_pst["LLM_error_spans"]}
		spans_esaai = {(x["start_i"], x["end_i"]) for x in df_user_pst["ESAAI-1_error_spans"]}
		if spans_gemba:
			data_agg[("gemba_agree", "pst")].append(len(spans_gemba & spans_esaai)/len(spans_gemba))
		else:
			data_agg[("gemba_agree", "pst")].append(1)
	
	# compare BAD and TGT
	line_bad = doc_bad.iloc[0]
	line_tgt = doc_tgt.iloc[0]

	data_agg[("bad", "esa_score")].append(line_bad["ESA-1_score"])
	data_agg[("tgt", "esa_score")].append(line_tgt["ESA-1_score"])
	data_agg[("bad", "esa_spans")].append(len(line_bad["ESA-1_error_spans"]))
	data_agg[("tgt", "esa_spans")].append(len(line_tgt["ESA-1_error_spans"]))
	data_agg[("OK", "esa_spans")].append(len(line_bad["ESA-1_error_spans"])>len(line_tgt["ESA-1_error_spans"]))
	data_agg[("OK", "esa_score")].append(line_bad["ESA-1_score"] < line_tgt["ESA-1_score"])
	data_agg[("OK", "esa_mark")].append(did_mark_perturbation(line_bad, line_tgt, "ESA-1"))

	data_agg[("bad", "esaai_score")].append(line_bad["ESAAI-1_score"])
	data_agg[("tgt", "esaai_score")].append(line_tgt["ESAAI-1_score"])
	data_agg[("bad", "esaai_spans")].append(len(line_bad["ESAAI-1_error_spans"]))
	data_agg[("tgt", "esaai_spans")].append(len(line_tgt["ESAAI-1_error_spans"]))
	data_agg[("OK", "esaai_score")].append(line_bad["ESAAI-1_score"] < line_tgt["ESAAI-1_score"])
	data_agg[("OK", "esaai_spans")].append(len(line_bad["ESAAI-1_error_spans"])>len(line_tgt["ESAAI-1_error_spans"]))
	data_agg[("OK", "esaai_mark")].append(did_mark_perturbation(line_bad, line_tgt, "ESAAI-1"))

	data_agg[("bad", "mqm_spans")].append(len(line_bad["MQM-1_error_spans"]))
	data_agg[("tgt", "mqm_spans")].append(len(line_tgt["MQM-1_error_spans"]))
	data_agg[("tgt", "mqm_score")].append(mqm_like_score(line_tgt["MQM-1_error_spans"]))
	data_agg[("bad", "mqm_score")].append(mqm_like_score(line_bad["MQM-1_error_spans"]))
	data_agg[("OK", "mqm_spans")].append(len(line_bad["MQM-1_error_spans"])>len(line_tgt["MQM-1_error_spans"]))
	data_agg[("OK", "mqm_score")].append(mqm_like_score(line_bad["MQM-1_error_spans"])<mqm_like_score(line_tgt["MQM-1_error_spans"]))
	data_agg[("OK", "mqm_mark")].append(did_mark_perturbation(line_bad, line_tgt, "MQM-1"))


data_agg = {
	k:np.average(v) for k, v in data_agg.items()
}

prev_k = None
for k, v in data_agg.items():
	if prev_k != k[1].split("_")[0]:
		print()
		prev_k = k[1].split("_")[0]
	print(f"{'-'.join(k):>20}: {v:.3f}")