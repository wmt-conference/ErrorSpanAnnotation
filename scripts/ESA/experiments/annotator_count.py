from ESA.annotation_loader import AnnotationLoader
PROTOCOLS = ["ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2"]
df = AnnotationLoader(refresh_cache=False).get_view(PROTOCOLS, only_overlap=False).dropna()
import collections

annotators = collections.defaultdict(set)

for _, row in df.iterrows():
    for protocol in PROTOCOLS:
        annotators[protocol].add(row[protocol+"_AnnotatorID"])

print({k: len(v) for k, v in annotators.items()})

