from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view()
import numpy as np
import pandas as pd

df_new = []

def get_spans(spans):
      return {(x["start_i"], x["end_i"]) for x in spans}

for _, row in df.iterrows():
    spans_gemba = get_spans(row["LLM_error_spans"])
    spans_esaai = get_spans(row["ESAAI-1_error_spans"])

    df_new.append({
          "gemba": len(spans_gemba),
          "kept": len(spans_gemba & spans_esaai),
          "removed": len(spans_gemba-spans_esaai),
          "added": len(spans_esaai-spans_gemba),
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
        f"{gemba_count} ({np.average(index):.1%})".replace("%", "\\%"),
        # perc_average((df_local.removed >= 3)),
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