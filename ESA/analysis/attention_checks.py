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

for documentID, doc_bad in df_bad.groupby(by="documentID"):
    if re.match(r".*#duplicate\d+", documentID):
        continue
    documentID = re.sub(r"#bad\d+$", "", doc_bad.iloc[0]["documentID"])

    doc_tgt = df_tgt[(df_tgt.documentID == documentID) & (df_tgt.login_gemba == doc_bad.iloc[0]["login_gemba"])]

    doc_bad = doc_bad.sort_values(by="itemID")
    doc_tgt = doc_tgt.sort_values(by="itemID")
    
    assert len(doc_bad) == len(doc_tgt)

    for (_, line_bad), (_, line_tgt) in zip(doc_bad.iterrows(), doc_tgt.iterrows()):
        data_agg[("bad", "esa_score")].append(line_bad["score_esa"])
        data_agg[("tgt", "esa_score")].append(line_tgt["score_esa"])
        data_agg[("bad", "esa_spans")].append(len(json.loads(line_bad["span_errors_esa"])))
        data_agg[("tgt", "esa_spans")].append(len(json.loads(line_tgt["span_errors_esa"])))
        data_agg[("comp", "esa_score")].append(line_bad["score_esa"] < line_tgt["score_esa"])
        data_agg[("comp", "esa_spans")].append(len(json.loads(line_bad["span_errors_esa"]))>len(json.loads(line_tgt["span_errors_esa"])))


        data_agg[("bad", "gesa_score")].append(line_bad["score_gemba"])
        data_agg[("tgt", "gesa_score")].append(line_tgt["score_gemba"])
        data_agg[("bad", "gesa_spans")].append(len(json.loads(line_bad["span_errors_gemba"])))
        data_agg[("tgt", "gesa_spans")].append(len(json.loads(line_tgt["span_errors_gemba"])))
        data_agg[("comp", "gesa_score")].append(line_bad["score_gemba"] < line_tgt["score_gemba"])
        data_agg[("comp", "gesa_spans")].append(len(json.loads(line_bad["span_errors_gemba"]))>len(json.loads(line_tgt["span_errors_gemba"])))

data_agg = {
    k:np.average(v) for k, v in data_agg.items()
}

for k, v in data_agg.items():
    print(f"{'-'.join(k):>20}: {v:.3f}")