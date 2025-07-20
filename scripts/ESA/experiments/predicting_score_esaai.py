from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=False).dropna()
import numpy as np
from sklearn.linear_model import LinearRegression, HuberRegressor
import scipy.stats

def featurize_line(x):
	val_tgt, val_spans = x
	
	return [
		len([x for x in val_spans if x["severity"] == "minor"]),
		len([x for x in val_spans if x["severity"] == "major"]),
		len([x for x in val_spans if x["end_i"] == "missing"]),
	]

def fit_lr(df, data_true):
	data_x = [featurize_line(x) for x in df.values]
	model = LinearRegression()
	model.fit(data_x, data_true)

	return [x+100 for x in model.predict(data_x)]

df = df[~ df.hypothesis.isnull()]

esaai2_true = [x["ESAAI-2_score"] for _, x in df.iterrows()]
esaai1_true = [x["ESAAI-1_score"] for _, x in df.iterrows()]

esaai2_predby_esaai1 = fit_lr(df[["hypothesis", "ESAAI-1_error_spans"]], esaai2_true)
esaai2_predby_gemba = fit_lr(df[["hypothesis", "LLM_error_spans"]], esaai2_true)
esaai1_predby_esaai1 = fit_lr(df[["hypothesis", "ESAAI-1_error_spans"]], esaai1_true)
esaai1_predby_gemba = fit_lr(df[["hypothesis", "LLM_error_spans"]], esaai1_true)


def latex_line(name, data_pred, data_true):
	val_corr = scipy.stats.pearsonr(data_pred, data_true)[0]
	print(
		name,
		f"{val_corr:.3f}",
		sep=" & ", end=" \\\\\n"
	)

latex_line("ESAAI1->ESAAI1", esaai1_true, esaai1_predby_esaai1)
latex_line("GEMBA->ESAAI1 ", esaai1_true, esaai1_predby_gemba)
latex_line("ESAAI1->ESAAI2", esaai2_true, esaai2_predby_esaai1)
latex_line("GEMBA->ESAAI2 ", esaai2_true, esaai2_predby_gemba)