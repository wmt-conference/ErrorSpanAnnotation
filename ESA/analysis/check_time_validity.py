print("WARNING: This is just to test possible errors in Appraise data collection.")

import csv

data = list(csv.reader(open("campaign-ruction-rc5/240315rc5ESA.scores.csv", "r")))
data = [(x[0], float(x[10]), float(x[11]), x[2]) for x in data]
for user in {x[0] for x in data}:
    data_local = [(x[1], x[2]) for x in data if x[0] == user]
    time_naive = 0
    for line in data_local:
        time_naive += line[1] - line[0]
        if line[1] - line[0] > 10*60:
            print("X", (line[1] - line[0])//60)
        if line[0] > line[1]:
            print("ERROR, negative duration!")
    print(user, time_naive//60)