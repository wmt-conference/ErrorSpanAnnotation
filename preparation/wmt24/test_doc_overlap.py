import json

data = json.load(open("data/wmt24_general/batches/wave0.en-cs.json", "r"))
for task in data:
    # allow viewing documents consequtively
    docsys_prev = None
    docsys_visited = set()
    for item in task["items"]:
        docsys = (item["documentID"], item["targetID"])
        if docsys in docsys_visited and docsys_prev != docsys:
            print("Duplicate document in task", task["task"]["batchNo"], docsys)
        docsys_prev = docsys
        docsys_visited.add(docsys)

    # make sure that tutorial is not modified and only at the beginning
    assert "#bad" not in item["documentID"] or "tutorial" not in item["documentID"]
    assert max(item_i for item_i, item in enumerate(task["items"]) if "tutorial" in item["documentID"]) <= 10
