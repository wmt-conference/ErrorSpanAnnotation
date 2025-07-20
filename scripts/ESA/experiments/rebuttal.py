from ESA.annotation_loader import AnnotationLoader
df = AnnotationLoader(refresh_cache=False).get_view(["LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"], only_overlap=True)

for row_i, row in df.iterrows():
	if len(row["source"].split()) > 20:
		continue
	# if len(row["LLM_error_spans"]) == 0 and len(row["ESA-1_error_spans"]) > 0:
	# if len(row["LLM_error_spans"]) > 0 and len(row["ESA-1_error_spans"]) == 0:

	def get_error_words(tgt, esa):
		return [(tgt[x["start_i"]:x["end_i"]+1], x["severity"]) for x in esa if x["end_i"] != "missing"]
	
	if len(row["LLM_error_spans"]) > 1 and len(row["ESA-1_error_spans"]) > 1:
		print(row["source"])
		print(row["hypothesis"])
		print(get_error_words(row["hypothesis"], row["LLM_error_spans"]))
		print(get_error_words(row["hypothesis"], row["ESA-1_error_spans"]))
		print()