import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import numpy as np
import json

df = MergedAnnotations().df


def mqm_like_score(spans):
    return -sum([{"critical": 25, "major": 5, "minor": 1, "undecided": 0}[x["severity"]] for x in spans])

def featurize_line(x):
    val_tgt, val_spans = x
    val_spans = json.loads(val_spans)
    f_span_len = np.average([int(x["end_i"]) - int(x["start_i"]) for x in val_spans if x["end_i"] != "missing"])
    f_span_len = f_span_len if not np.isnan(f_span_len) else 0
    
    return [
        len(str(val_tgt).split()),
        # average error span length
        f_span_len,
        # number of minor and major errors
        len([x for x in val_spans if x["severity"] == "minor"]),
        len([x for x in val_spans if x["severity"] == "major"]),
        len([x for x in val_spans if x["end_i"] == "missing"]),
    ]

def fit_lr(df, data_true):
    from sklearn.linear_model import LinearRegression
    data_x = [featurize_line(x) for x in df.values]

    model = LinearRegression()
    model.fit(data_x, data_true)
    print(model.coef_)
    return model.predict(data_x)


esa_true = [x.score_esa for _, x in df.iterrows()]
mqm_pred_mqm = [mqm_like_score(json.loads(x.span_errors_mqm)) for _, x in df.iterrows()]
esa_pred_mqm = [mqm_like_score(json.loads(x.span_errors_esa)) for _, x in df.iterrows()]
mqm_pred_lor = fit_lr(df[["translation_seg", "span_errors_mqm"]], esa_true)
esa_pred_lor = fit_lr(df[["translation_seg", "span_errors_esa"]], esa_true)

import scipy.stats
import sklearn.metrics

def latex_line(name, data_pred, data_true):
    val_corr = scipy.stats.pearsonr(data_pred, data_true)[0]
    # best affine fit
    data_pred_norm = scipy.stats.zscore(data_pred)*np.std(data_true)+np.mean(data_true)
    val_mae = sklearn.metrics.mean_absolute_error(data_pred_norm, data_true)
    print(
        name,
        f"{val_corr:.2f}",
        f"{val_mae:.2f}",
        sep=" & ", end=" \\\\\n"
    )

latex_line("ESA", esa_pred_mqm, esa_true)
latex_line("ESA", esa_pred_lor, esa_true)
latex_line("MQM", mqm_pred_mqm, esa_true)
latex_line("MQM", mqm_pred_lor, esa_true)