from annotations import AppraiseAnnotations


anno_esa = AppraiseAnnotations("campaign-ruction-rc5/240315rc5ESA.scores.csv", "ESA").generate_scores()
print(anno_esa.df.columns)