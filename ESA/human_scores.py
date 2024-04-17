import ipdb
import pandas as pd
from scipy.stats import ranksums
from itertools import combinations
import matplotlib.pyplot as plt


class HumanScores:
    def __init__(self, language_pair):
        self.language_pair = language_pair
        self.resources = None

        # load protocol
        scores = {}
        systems = []
        for protocol in ["wmt-mqm", "wmt-dasqm", "esa", "mqm", "gemba", "esa_severity", "gemba_severity"]:
            if protocol == "wmt-mqm":
                path = f"data/mt-metrics-eval-v2/wmt23/human-scores/{language_pair}.mqm.seg.score"
            elif protocol == "wmt-dasqm":
                path = f"data/mt-metrics-eval-v2/wmt23/human-scores/{language_pair}.da-sqm.seg.score"
            elif protocol == "esa":
                path = f"campaign-ruction-rc5/{language_pair}.ESA.seg.score"
            elif protocol == "mqm":
                path = f"campaign-ruction-rc5/{language_pair}.MQM.seg.score"
            elif protocol == "gemba":
                path = f"campaign-ruction-rc5/{language_pair}.GEMBA.seg.score"
            elif protocol == "esa_severity":
                path = f"campaign-ruction-rc5/{language_pair}.ESA_severity.seg.score"
            elif protocol == "gemba_severity":
                path = f"campaign-ruction-rc5/{language_pair}.GEMBA_severity.seg.score"

            scores["system"] = pd.read_csv(path, sep="\t", header=None, names=["system", "score"])['system']
            scores[protocol] = pd.read_csv(path, sep="\t", header=None, names=["system", "score"])['score']

        # merge scores
        self.resources = pd.DataFrame(scores)

    def generate_ranks(self):
        df = self.resources
        # replace in all columns string "None" with NaN
        df = df.replace("None", float("nan"))
        df = df.dropna()

        # convert all scores to float
        for col in df.columns:
            if col != "system":
                df[col] = df[col].astype(float)
        # group by system
        df2 = df.groupby("system").mean()
        df2.groupby("system").mean().to_excel("delme2.xlsx")


        results = {}
        data = {}
        data_clusters = {}
        # for scheme in ["wmt-mqm", "wmt-dasqm", "esa", "gemba", "mqm", "esa_severity", "gemba_severity"]:
        for scheme in ["wmt-mqm", "wmt-dasqm", "esa", "mqm", "esa_severity"]:
            # Step 1: Calculate average scores for each system
            system_scores = df[['system', scheme]].groupby('system')[scheme].agg(['mean', list]).rename(columns={'list': 'scores'})
            # sort by mean score
            system_scores = system_scores.sort_values(by='mean', ascending=False)

            # Step 2: Perform Wilcoxon rank-sum tests for each pair of systems
            p_values = pd.DataFrame(index=system_scores.index, columns=system_scores.index)
            for (sys1, scores1), (sys2, scores2) in combinations(system_scores.iterrows(), 2):
                stat, p_value = ranksums(scores1['scores'], scores2['scores'], alternative='greater')
                p_values.at[sys1, sys2] = p_value
                p_values.at[sys2, sys1] = p_value

            # Fill diagonal with 0s for easier interpretation
            p_values = p_values.fillna(1)  # assume no significant difference with itself

            data[scheme] = {"system": [], scheme: []}
            data_clusters[scheme] = []
            for i, system in enumerate(system_scores.index):
                cluster = [sys for sys in system_scores.index[i+1:] if p_values.at[system, sys] >= 0.05]
                if len(cluster) == 0 and i < len(system_scores) - 1:
                    threshold = system_scores.at[system, 'mean'] - (system_scores.at[system, 'mean'] - system_scores.at[system_scores.index[i + 1], 'mean'])/2
                    data_clusters[scheme].append(threshold)
                    


                data[scheme]["system"].append(system)
                data[scheme][scheme].append(system_scores.at[system, 'mean'])

        plot_clusters(data, data_clusters)
       
def plot_clusters(data, data_clusters):
    # Create a figure with subplots for each schema
    columns = int((len(data) - 1)/2)
    fig, axs = plt.subplots(2, columns, figsize=(4 * columns, 8)) 
    axs = axs.flatten() 

    i = 0
    for _, scheme in enumerate(data):
        if scheme == "wmt-mqm":
            continue
        df1 = pd.DataFrame(data["wmt-mqm"])
        # set index to "systems"
        df1.set_index("system", inplace=True)
        df2 = pd.DataFrame(data[scheme])
        df2.set_index("system", inplace=True)

        # merge the two dataframes
        df = pd.merge(df1, df2, left_index=True, right_index=True)
        
        # Plotting the scatter plots for each dataset
        df.plot.scatter(x=scheme, y="wmt-mqm", ax=axs[i], color='black')
        
        # Ensuring x-axis only shows whole numbers
        axs[i].xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # Adding titles with language pairs or other identifiers
        axs[i].set_title(f"Scatter plot for {scheme}")
        
        # Plotting vertical lines for scheme clusters and horizontal for MQM
        for cluster in data_clusters[scheme]:
            axs[i].axvline(cluster, color="red", linestyle="--")
        for cluster in data_clusters["wmt-mqm"]:
            axs[i].axhline(cluster, color="blue", linestyle="--")
        i += 1

    plt.tight_layout()
    subname = "_gemba" if "gemba" in data else ""
    plt.savefig(f"generated_plots/clusters_esa{subname}.pdf")
