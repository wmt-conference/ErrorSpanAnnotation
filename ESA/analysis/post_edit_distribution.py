import ESA.settings
ESA.settings.PROJECT = "GEMBA"
from ESA.merged_annotations import MergedAnnotations
import numpy as np
import json
import collections
import pandas as pd

df = MergedAnnotations().df

df_new = []


def get_spans(spans):
      return {(x["start_i"], x["end_i"]) for x in spans}

for _, row in df.iterrows():
    if type(row.gemba_mqm_span_errors_gemba) != list:
            continue
    
    spans_gemba = get_spans(row.gemba_mqm_span_errors_gemba)
    spans_gesa = get_spans(json.loads(row.span_errors_gemba))

    df_new.append({
          "gemba": len(spans_gemba),
          "kept": len(spans_gemba & spans_gesa),
          "removed": len(spans_gemba-spans_gesa),
          "added": len(spans_gesa-spans_gemba),
    })

df_new = pd.DataFrame.from_dict(df_new)

def perc_average(arr):
    return f"{np.average(arr):.0%}".replace("%", "\\%")
def get_line(gemba_count, operation="equal"):
    if operation == "equal":
        index = df_new.gemba == gemba_count
    elif operation == "greater_than":
        index = df_new.gemba >= gemba_count
    df_local = df_new[index]


    print(
        f"{np.average(index):.1%}".replace("%", "\\%"),
        gemba_count,
        perc_average((df_local.removed >= 3)),
        perc_average((df_local.removed == 2)),
        perc_average((df_local.removed == 1)),
        perc_average((df_local.removed == 0)),
        perc_average((df_local.removed == 0) & (df_local.added == 0)),
        perc_average((df_local.added == 0)),
        perc_average((df_local.added == 1)),
        perc_average((df_local.added == 2)),
        perc_average((df_local.added >= 3)),
        sep=" & ",
        end="\\\\\n"
    )

get_line(gemba_count=0)
get_line(gemba_count=1)
get_line(gemba_count=2)
get_line(gemba_count=3)
get_line(gemba_count=4, operation="greater_than")