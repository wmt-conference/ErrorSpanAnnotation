import ipdb
import pandas as pd
from scipy.stats import ranksums
from itertools import combinations
import matplotlib.pyplot as plt
from ESA.settings import methods, PROJECT


class HumanScores:
    def __init__(self, language_pair):
        self.language_pair = language_pair
        self.resources = None

        # load protocol
        scores = {}
        for protocol in ["llm", "wmt-mqm", "wmt-dasqm", "esa", "mqm", "gemba", "esa_severity", "gemba_severity"]:
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
            elif protocol == "llm":
                path = f"campaign-ruction-rc5/{language_pair}.LLM.seg.score"

            scores["system"] = pd.read_csv(path, sep="\t", header=None, names=["system", "score"])['system']
            scores[protocol] = pd.read_csv(path, sep="\t", header=None, names=["system", "score"])['score']

        # merge scores
        df = pd.DataFrame(scores)

        # replace in all columns string "None" with NaN
        # convert all scores to float
        for col in df.columns:
            if col != "system":
                df[col] = df[col].replace("None", float("nan")).astype(float)

        self.resources = df

    def generate_ranks(self):
        df = self.resources
        df = df.dropna()

        # group by system
        df2 = df.groupby("system").mean()
        df2.groupby("system").mean().to_excel("generated_plots/system_ranking.xlsx")

        data = {}
        data_clusters = {}
        list_of_schemes = ["wmt-mqm", "mqm", "wmt-dasqm", "esa"]
        if PROJECT == "GEMBA":
            list_of_schemes = ["wmt-mqm", "esa", "gemba", "llm"]

        for scheme in list_of_schemes:
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

        self.plot_clusters(data, data_clusters)

    def plot_clusters(self, data, data_clusters):
        import ESA.figutils as figutils

        figutils.matplotlib_default()

        # Create a figure with subplots for each schema
        rows = int((len(data) - 1)/3)
        columns = 3 #int((len(data) - 1)/2)
        rows = 1
        columns = len(data) - 1
        fig, axs = plt.subplots(rows, columns, figsize=(3 * columns, 2 * rows))

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
            # calculate pearson correlation
            corr = df.corr(method='pearson', numeric_only=True)['wmt-mqm'][scheme]

            # Plotting the scatter plots for each dataset
            df.plot.scatter(x=scheme, y="wmt-mqm", ax=axs[i], color='black')

            # rename x-axis and y-axis based on methods[scheme]
            axs[i].set_xlabel(methods[scheme]['name'])
            if i == 0:
                axs[i].set_ylabel(methods["wmt-mqm"]['name'], labelpad=-2)
            else:
                # use ylabel only for the first plot
                # the rest still needs ghost space
                axs[i].set_ylabel("$\,$", labelpad=-2)
            
            # Ensuring x-axis only shows whole numbers
            axs[i].xaxis.set_major_locator(plt.MaxNLocator(integer=True, nbins=8))

            # Plotting vertical lines for scheme clusters and horizontal for MQM
            for cluster in data_clusters[scheme]:
                axs[i].axvline(cluster, color=figutils.COLORS[0], linestyle="--")
            for cluster in data_clusters["wmt-mqm"]:
                axs[i].axhline(cluster, color=figutils.COLORS[2], linestyle="--")

            # Add correlation to the plot to the bottom right
            axs[i].text(0.95, 0.05, f"r={corr:.3f}", transform=axs[i].transAxes, ha='right', va='bottom')

            i += 1

        plt.tight_layout(pad=0.1, w_pad=0.5)
        subname = "gemba" if PROJECT == "GEMBA" else "esa"
        plt.savefig(f"PAPER/generated_plots/clusters_{subname}.pdf")

    def calculate_inter_annotator_with_mqm(self):
        df = self.resources
        df = df.dropna()
        print("-"*50)
        print(f"Intra-annotator agreement against WMT-MQM:")
        print(df.corr(method='kendall', numeric_only=True)['wmt-mqm'])
        print("-"*50)
