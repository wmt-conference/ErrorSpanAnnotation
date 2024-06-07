raise Exception("This code uses old loader, please refactor.")
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import json
import re
import collections
import numpy as np

df = MergedAnnotations().df

df_bad = df[df.is_bad=="BAD"]
df_tgt = df[df.is_bad=="TGT"]


data_agg = collections.defaultdict(list)


def mqm_like_score(spans):
	return 100-sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

for documentID, doc_bad in df_bad.groupby(by="documentID"):
	if re.match(r".*#duplicate\d+", documentID):
		continue
	documentID = re.sub(r"#bad\d+$", "", doc_bad.iloc[0]["documentID"])
	login_gemba = doc_bad.iloc[0]["login_gemba"]

	doc_tgt = df_tgt[(df_tgt.documentID == documentID) & (df_tgt.login_gemba == login_gemba)]


	doc_bad = doc_bad.sort_values(by="itemID")
	doc_tgt = doc_tgt.sort_values(by="itemID")

	# get previous and following documents
	df_user_pre = df[(df.login_gemba == login_gemba) & (df.itemID < doc_bad.iloc[0].itemID)].sort_values(by="itemID")
	df_user_pst = df[(df.login_gemba == login_gemba) & (df.itemID > doc_bad.iloc[-1].itemID)].sort_values(by="itemID")

	if len(df_user_pre) > 0 and len(df_user_pst) > 0:
		df_user_pre = df_user_pre[df_user_pre.documentID == df_user_pre.iloc[-1].documentID]
		df_user_pst = df_user_pst[df_user_pst.documentID == df_user_pst.iloc[0].documentID]

		for _, line in df_user_pre.iterrows():
			if type(line["gemba_mqm_span_errors_gemba"]) != list:
				continue
			spans_gemba = {(x["start_i"], x["end_i"]) for x in line["gemba_mqm_span_errors_gemba"]}
			spans_gesa = {(x["start_i"], x["end_i"]) for x in json.loads(line["span_errors_gemba"])}
			if spans_gemba:
				data_agg[("gemba_activity", "pre")].append(len(spans_gemba & spans_gesa)/len(spans_gemba))
			
		for _, line in df_user_pst.iterrows():
			if type(line["gemba_mqm_span_errors_gemba"]) != list:
				continue
			spans_gemba = {(x["start_i"], x["end_i"]) for x in line["gemba_mqm_span_errors_gemba"]}
			spans_gesa = {(x["start_i"], x["end_i"]) for x in json.loads(line["span_errors_gemba"])}
			if spans_gemba:
				data_agg[("gemba_activity", "pst")].append(len(spans_gemba & spans_gesa)/len(spans_gemba))
	
	assert len(doc_bad) == len(doc_tgt)

	for (_, line_bad), (_, line_tgt) in zip(doc_bad.iterrows(), doc_tgt.iterrows()):
		line_bad["span_errors_esa"] = json.loads(line_bad["span_errors_esa"])
		line_tgt["span_errors_esa"] = json.loads(line_tgt["span_errors_esa"])
		line_bad["span_errors_mqm"] = json.loads(line_bad["span_errors_mqm"])
		line_tgt["span_errors_mqm"] = json.loads(line_tgt["span_errors_mqm"])

		data_agg[("bad", "esa_time")].append(line_bad["duration_seconds_esa"])
		data_agg[("tgt", "esa_time")].append(line_tgt["duration_seconds_esa"])
		data_agg[("bad", "esa_score")].append(line_bad["score_esa"])
		data_agg[("tgt", "esa_score")].append(line_tgt["score_esa"])
		data_agg[("bad", "esa_spans")].append(len(line_bad["span_errors_esa"]))
		data_agg[("tgt", "esa_spans")].append(len(line_tgt["span_errors_esa"]))
		data_agg[("comp", "esa_spans")].append(len(line_bad["span_errors_esa"])>len(line_tgt["span_errors_esa"]))
		data_agg[("comp", "esa_score")].append(line_bad["score_esa"] < line_tgt["score_esa"])

		data_agg[("bad", "gesa_score")].append(line_bad["score_gemba"])
		data_agg[("tgt", "gesa_score")].append(line_tgt["score_gemba"])
		data_agg[("bad", "gesa_spans")].append(len(line_bad["span_errors_gemba"]))
		data_agg[("tgt", "gesa_spans")].append(len(line_tgt["span_errors_gemba"]))
		data_agg[("comp", "gesa_score")].append(line_bad["score_gemba"] < line_tgt["score_gemba"])
		data_agg[("comp", "gesa_spans")].append(len(line_bad["span_errors_gemba"])>len(line_tgt["span_errors_gemba"]))

		data_agg[("bad", "mqm_time")].append(line_bad["duration_seconds_mqm"])
		data_agg[("tgt", "mqm_time")].append(line_tgt["duration_seconds_mqm"])
		data_agg[("bad", "mqm_spans")].append(len(line_bad["span_errors_mqm"]))
		data_agg[("tgt", "mqm_spans")].append(len(line_tgt["span_errors_mqm"]))
		data_agg[("bad", "mqm_spans")].append(len(line_bad["span_errors_mqm"]))
		data_agg[("tgt", "mqm_spans")].append(len(line_tgt["span_errors_mqm"]))
		data_agg[("tgt", "mqm_score")].append(mqm_like_score(line_tgt["span_errors_mqm"]))
		data_agg[("bad", "mqm_score")].append(mqm_like_score(line_bad["span_errors_mqm"]))
		data_agg[("comp", "mqm_spans")].append(len(line_bad["span_errors_mqm"])>len(line_tgt["span_errors_mqm"]))
		data_agg[("comp", "mqm_score")].append(mqm_like_score(line_bad["span_errors_mqm"])<mqm_like_score(line_tgt["span_errors_mqm"]))


data_agg = {
	k:np.average(v) for k, v in data_agg.items()
}

prev_k = None
for k, v in data_agg.items():
	if prev_k != k[1].split("_")[0]:
		print()
		prev_k = k[1].split("_")[0]
	print(f"{'-'.join(k):>20}: {v:.3f}")