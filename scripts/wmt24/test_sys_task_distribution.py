import json

data = json.load(open("data/wmt24_general/batches/wave0.en-cs.json", "r"))
for task in data:
    systems = {item["targetID"] for item in task["items"]}
    print(
        f'TASK {task["task"]["batchNo"]:<4}',
        "DOCS-PER_SYS:",
        {sys: len({item["documentID"] for item in task["items"] if item["targetID"] == sys and "#" not in item["documentID"]}) for sys in systems}
    )