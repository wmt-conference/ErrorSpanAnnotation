import os
import ipdb
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ranksums
from itertools import combinations
from ESA.utils import PROTOCOL_DEFINITIONS
from ESA.annotation_loader import AnnotationLoader


def ClustersAndRanking(annotations_loader):
    df = annotations_loader.get_view()

    data = {}
    data_clusters = {}

    for protocol in PROTOCOL_DEFINITIONS.keys():
        protocol_scores = f"{protocol}_score"

        # Step 1: Calculate average scores for each system
        system_scores = df[['systemID', protocol_scores]].groupby('systemID')[protocol_scores].agg(['mean', list]).rename(columns={'list': 'scores'})
        # sort by mean score
        system_scores = system_scores.sort_values(by='mean', ascending=False)

        # Step 2: Perform Wilcoxon rank-sum tests for each pair of systems
        p_values = pd.DataFrame(index=system_scores.index, columns=system_scores.index)
        for (sys1, scores1), (sys2, scores2) in combinations(system_scores.iterrows(), 2):
            stat, p_value = ranksums(scores1['scores'], scores2['scores'], alternative='greater')
            p_values.at[sys1, sys2] = p_value
            p_values.at[sys2, sys1] = p_value

        # Fill diagonal with 1s for easier interpretation
        p_values = p_values.fillna(1)  # assume no significant difference with itself

        data[protocol] = {"system": [], protocol: []}
        data_clusters[protocol] = []
        for i, system in enumerate(system_scores.index):
            cluster = [sys for sys in system_scores.index[i+1:] if p_values.at[system, sys] >= 0.05]
            if len(cluster) == 0 and i < len(system_scores) - 1:
                # if there is cluster divider, make the point in the middle between the two neighboring systems
                threshold = system_scores.at[system, 'mean'] - (system_scores.at[system, 'mean'] - system_scores.at[system_scores.index[i + 1], 'mean'])/2
                data_clusters[protocol].append(threshold)

            data[protocol]["system"].append(system)
            data[protocol][protocol].append(system_scores.at[system, 'mean'])

    plot_clusters(data, data_clusters, ["MQM-1", "ESA-1", "WMT-DASQM"], "PAPER_ESA/generated_plots/ranking_and_clusters.pdf")
    plot_clusters(data, data_clusters, ["ESA-1", "ESAAI-1", "LLM"], "PAPER_ESAAI/generated_plots/ranking_and_clusters.pdf")
    plot_clusters(data, data_clusters, ["MQM-1", "LLM", "ESA-1", "ESAAI-1", "ESA-2", "ESAAI-2", "WMT-DASQM"], "archive/all.pdf")


def plot_clusters(data, data_clusters, protocols, filename):
    import ESA.figutils as figutils

    figutils.matplotlib_default()

    rows = 1
    columns = len(protocols)
    fig, axs = plt.subplots(rows, columns, figsize=(3 * columns, 2.5 * rows))

    axs = axs.flatten()

    i = 0
    for protocol in protocols:
        df1 = pd.DataFrame(data["WMT-MQM"])
        # set index to "systems"
        df1.set_index("system", inplace=True)

        df2 = pd.DataFrame(data[protocol])
        df2.set_index("system", inplace=True)

        # merge the two dataframes
        df = pd.merge(df1, df2, left_index=True, right_index=True)
        corr = df.corr(method='kendall')["WMT-MQM"][protocol]

        # Plotting the scatter plots for each dataset
        df.plot.scatter(x=protocol, y="WMT-MQM", ax=axs[i], color='black')
        # Add correlation to the plot to the bottom right
        axs[i].text(0.95, 0.05, f"ρ={corr:.3f}", transform=axs[i].transAxes, ha='right', va='bottom')

        if protocol in ["ESA-1", "ESAAI-1"]:
            protocol2 = protocol.replace("1", "2")
            df3 = pd.DataFrame(data[protocol2])
            df3.set_index("system", inplace=True)
            df = pd.merge(df1, df3, left_index=True, right_index=True)
            corr = df.corr(method='kendall')["WMT-MQM"][protocol2]
            df.plot.scatter(x=protocol2, y="WMT-MQM", ax=axs[i], color=figutils.COLORS[1])
            axs[i].text(0.95, 0.15, f"ρ={corr:.3f}", transform=axs[i].transAxes, ha='right', va='bottom', color=figutils.COLORS[1])
        else:
            # Plotting vertical lines for scheme clusters and horizontal for MQM
            for cluster in data_clusters[protocol]:
                axs[i].axvline(cluster, color=figutils.COLORS[0], linestyle="--")
            for cluster in data_clusters["WMT-MQM"]:
                axs[i].axhline(cluster, color=figutils.COLORS[2], linestyle="--")

        axs[i].set_xlabel(PROTOCOL_DEFINITIONS[protocol]['name'].replace("_1", "").replace("$$", ""))
        if i == 0:
            axs[i].set_ylabel(PROTOCOL_DEFINITIONS["WMT-MQM"]['name'], labelpad=-2)
        else:
            # use ylabel only for the first plot
            # the rest still needs ghost space
            axs[i].set_ylabel("$\,$", labelpad=-2)

        # Ensuring x-axis only shows whole numbers
        axs[i].xaxis.set_major_locator(plt.MaxNLocator(integer=True, nbins=8))

        i += 1

    plt.tight_layout(pad=0.1, w_pad=0.5)
    # create parent folders
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename)



# def calculate_inter_annotator_with_mqm(self):
#     df = self.resources
#     df = df.dropna()
#     print("-"*50)
#     print(f"Intra-annotator agreement against WMT-MQM:")
#     print(df.corr(method='kendall', numeric_only=True)['wmt-mqm'])
#     print("-"*50)


if __name__ == '__main__':
    ClustersAndRanking(AnnotationLoader(refresh_cache=False))
