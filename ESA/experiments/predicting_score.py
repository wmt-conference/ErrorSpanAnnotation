raise Exception("This code uses old loader, please refactor.")
import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import numpy as np
import json

df = MergedAnnotations().df

from sklearn.linear_model import LinearRegression, HuberRegressor

def mqm_like_score(spans):
	return 100-sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

def safe_avg(arr):
	if not arr:
		return 0
	else:
		return np.average(arr)

def featurize_line(x):
	val_tgt, val_spans = x
	if type(val_spans) is not list:
		val_spans = json.loads(val_spans)
	f_span_len = safe_avg([int(x["end_i"]) - int(x["start_i"]) for x in val_spans if x["end_i"] != "missing"])
	tgt_len = len(str(val_tgt).split())
	f_len_major = sum([int(x["end_i"]) - int(x["start_i"]) for x in val_spans if x["end_i"] != "missing" and x["severity"] == "major"])
	f_len_minor = sum([int(x["end_i"]) - int(x["start_i"]) for x in val_spans if x["end_i"] != "missing" and x["severity"] == "minor"])
	
	return [
		# tgt_len,
		# average error span length
		f_span_len,
		# f_len_major/tgt_len,
		# f_len_minor/tgt_len,
		# number of minor and major errors
		len([x for x in val_spans if x["severity"] == "minor"]),
		len([x for x in val_spans if x["severity"] == "major"]),
		len([x for x in val_spans if x["end_i"] == "missing"]),
		len([x for x in val_spans if x["severity"] == "minor"])/tgt_len,
		len([x for x in val_spans if x["severity"] == "major"])/tgt_len,
		len([x for x in val_spans if x["end_i"] == "missing"])/tgt_len,
	]

def fit_lr(df, data_true, force_coef=None):
	data_x = [featurize_line(x) for x in df.values]

	for f_i in range(len(data_x[0])):
		data_f = [x[f_i] for x in data_x]
		print(f"{f_i}:{np.corrcoef(data_f, data_true)[0,1]:.2f}", end="  ")
	print()

	# set baseline to 0 so that we have control over the intercept
	data_true = np.array(data_true)-100
	model = HuberRegressor(fit_intercept=False, epsilon=1.01)
	model.fit(data_x, data_true)
	print(", ".join([f"{x:.1f}" for x in model.coef_]))

	if force_coef:
		model.coef_ = np.array(force_coef)
	return [x+100 for x in model.predict(data_x)]

df = df[~ df.hypothesis.isnull()]

esa_true = [x.score_esa for _, x in df.iterrows()]
gesa_true = [x.score_gemba for _, x in df.iterrows()]
mqm_pred_mqm = [mqm_like_score(json.loads(x.span_errors_mqm)) for _, x in df.iterrows()]
esa_pred_mqm = [mqm_like_score(json.loads(x.span_errors_esa)) for _, x in df.iterrows()]
gesa_pred_mqm = [mqm_like_score(x["LLM_error_spans"]) for _, x in df.iterrows()]
mqm_pred_lor = fit_lr(df[["hypothesis", "span_errors_mqm"]], esa_true)
esa_pred_lor = fit_lr(df[["hypothesis", "span_errors_esa"]], esa_true)
esa_pred_lor_gesa = fit_lr(df[["hypothesis", "span_errors_esa"]], gesa_true)
esa_pred_lor_reg = fit_lr(df[["hypothesis", "span_errors_esa"]], esa_true, force_coef=[-0.2, -5.1, -11.7, -16.5, -71.9, -217.6, -48.5])
gesa_pred_lor = fit_lr(df[["hypothesis", "gemba_mqm_span_errors_gemba"]], esa_true)
gesa_pred_lor_reg = fit_lr(df[["hypothesis", "gemba_mqm_span_errors_gemba"]], esa_true, force_coef=[-0.2, -5.1, -11.7, -16.5, -71.9, -217.6, -48.5])
gesa_pred_lor_gesa = fit_lr(df[["hypothesis", "gemba_mqm_span_errors_gemba"]], gesa_true)
gesa_pred_lor_reg_gesa = fit_lr(df[["hypothesis", "gemba_mqm_span_errors_gemba"]], gesa_true, force_coef=[-0.2, -5.1, -11.7, -16.5, -71.9, -217.6, -48.5])

import scipy.stats
import sklearn.metrics

def latex_line(name, data_pred, data_true):
	val_corr = scipy.stats.pearsonr(data_pred, data_true)[0]
	val_mae = sklearn.metrics.mean_absolute_error(data_pred, data_true)
	print(
		name,
		f"{val_corr:.2f}",
		f"{val_mae:.2f}",
		sep=" & ", end=" \\\\\n"
	)

latex_line("ESA-GESA", esa_true, gesa_true)
latex_line("ESA", esa_pred_mqm, esa_true)
latex_line("ESA", esa_pred_mqm, gesa_true)
latex_line("ESA", esa_pred_lor, esa_true)
latex_line("ESA", esa_pred_lor_gesa, gesa_true)
latex_line("MQM", mqm_pred_mqm, esa_true)
latex_line("MQM", mqm_pred_mqm, gesa_true)
latex_line("MQM", mqm_pred_lor, esa_true)
latex_line("GESA", gesa_pred_mqm, esa_true)
latex_line("GESA", gesa_pred_mqm, gesa_true)
latex_line("GESA", gesa_pred_lor, esa_true)
latex_line("GESA", gesa_pred_lor_gesa, gesa_true)
latex_line("GESA", gesa_pred_lor_reg, esa_true)
latex_line("GESA", gesa_pred_lor_reg_gesa, gesa_true)