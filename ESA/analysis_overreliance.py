from merged_annotations import MergedAnnotations
import matplotlib.pyplot as plt
import figutils

figutils.matplotlib_default()

df = MergedAnnotations().df

print(df)