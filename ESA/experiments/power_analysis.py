import pandas as pd
import ipdb
from itertools import combinations
from scipy.stats import ranksums, mannwhitneyu
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from tqdm import tqdm
import json
from ESA.annotation_loader import AnnotationLoader
from statsmodels.formula.api import mixedlm

def get_observable_minimum_detectable_effect(df, protocol, alpha=0.05, beta=0.95):
    pvalues = []
    for sys1, sys2 in combinations(df['systemID'].unique(), 2):
        sys1_scores = df[df['systemID'] == sys1][f'{protocol}_score']
        sys2_scores = df[df['systemID'] == sys2][f'{protocol}_score']
        if sys1_scores.mean() < sys2_scores.mean():
            sys1_scores, sys2_scores = sys2_scores, sys1_scores

        diff = sys1_scores.mean() - sys2_scores.mean()
        _, p_value = mannwhitneyu(sys1_scores, sys2_scores, alternative='greater')
        pvalues.append([p_value < alpha, diff])

    pdf = pd.DataFrame(pvalues, columns=['pvalue', 'diff']).sort_values(by='diff', ascending=True)

    for mde in pdf['diff'].unique():
        subdf = pdf[pdf['diff'] >= mde]

        observed_accuracy = subdf['pvalue'].sum()/len(subdf)
        if observed_accuracy >= beta:
            print(f"Observable MDE for {protocol} is {mde:.2f}")
            return mde


def effect_size_for_n_clusters(df, protocol):
    df = annotations.get_view(protocols=[protocol]).dropna()

    sys_scores = df[['systemID', f'{protocol}_score']].groupby('systemID')[f'{protocol}_score'].agg(['mean', list]).rename(columns={'list': 'scores'})['mean']
    sys_scores = sys_scores.sort_values(ascending=True)

    # calculate differences between neighboring systems
    diffs = []
    for i in range(1, len(sys_scores)):
        diffs.append(sys_scores[i] - sys_scores[i-1])

    ddf = pd.DataFrame(diffs, columns=['diff'])
    ddf = ddf.sort_values(by='diff', ascending=False).reset_index(drop=True)

    clusters_effect_sizes = {}
    for i, row in ddf.iterrows():
        clusters_effect_sizes[int(i) + 2] = row['diff']

    return clusters_effect_sizes


def calculate_power(sample_size, params, alpha, num_simulations=1000, operator="greater"):
    k = None
    if len(params) == 2:
        k, theta = params

    rejections = 0
    for _ in range(num_simulations):
        # Generate two sets of samples from the distribution
        if k is None:
            # sample from data
            subdf = params.sample(sample_size, replace=True)
            data1 = list(subdf["sys1"])
            data2 = list(subdf["sys2"])
        else:
            data1 = np.random.gamma(k[0], theta[0], sample_size)
            data2 = np.random.gamma(k[1], theta[1], sample_size)

        t_stat, p_value = mannwhitneyu(data1, data2, alternative=operator)

        # Check if null hypothesis is rejected
        if p_value < alpha:
            rejections += 1

    # Calculate the power
    power = rejections / num_simulations
    return power


# Use Bisection Method to Determine Sample Size
def find_sample_size(params, alpha, desired_power, lower=1, upper=20000, num_simulations=1000, operator="greater"):
    while lower < upper:
        mid = (lower + upper) // 2
        power = calculate_power(mid, params, alpha, num_simulations=num_simulations, operator=operator)

        if abs(power - desired_power) < 0.001:
            return mid, power
        elif power < desired_power:
            lower = mid + 1
        else:
            upper = mid - 1

    return mid, power



def calculate_sample_size_for_clusters(sample_sizes, sys_diffs):
    clusters = {}
    sysdf = pd.DataFrame([sys_diffs]).T.sort_values(by=0, ascending=False)
    df = pd.DataFrame(sample_sizes).sort_values(by=1, ascending=False)
    df["key"] = df[0].apply(lambda x: f"{x[0]}_{x[1]}")
    df.set_index("key", inplace=True)

    for samples in df[1].unique():
        # with this number of samples, how many clusters would we have?
        cluster_count = 1
        for i, system in enumerate(sysdf.index):
            # if system is significantly better than the rest of systems with lower score, it is in the different cluster
            no_enough = [sys for sys in sysdf.index[i+1:] if df.loc[f"{system}_{sys}"][1] > samples]
            if len(no_enough) == 0 and i < len(sysdf) - 1:
                cluster_count += 1

        if cluster_count == 1 or cluster_count == len(sysdf):
            continue

        # since samples are ordered, there was smaller number of samples needed
        clusters[cluster_count] = samples
    return clusters


def power_analysis(df, protocol, alpha=0.05, desired_power=0.8, num_simulations=1000):
    # for each system pair, we calculate sample size needed to detect their effect size
    sample_sizes = []
    sys_diffs = {}
    for system in df['systemID'].unique():
        sys_diffs[system] = df[df['systemID'] == system][f'{protocol}_score'].mean()

    operator = "greater"
    if "MQM" in protocol:
        # multiply scores by -1 to have them on the same scale and swap operators
        df[f'{protocol}_score'] = df[f'{protocol}_score'] * -1
        operator = "less"

    for sys1, sys2 in tqdm(list(combinations(df['systemID'].unique(), 2))):
        sys1_mean = df[df['systemID'] == sys1][f'{protocol}_score'].mean()
        sys2_mean = df[df['systemID'] == sys2][f'{protocol}_score'].mean()
        sys1_var = df[df['systemID'] == sys1][f'{protocol}_score'].var()
        sys2_var = df[df['systemID'] == sys2][f'{protocol}_score'].var()
        if (operator == "greater" and (sys1_mean < sys2_mean)) or (operator == "less" and (sys1_mean > sys2_mean)):
            sys1, sys2 = sys2, sys1
            sys1_mean, sys2_mean = sys2_mean, sys1_mean
            sys1_var, sys2_var = sys2_var, sys1_var

        k_s = [sys1_mean**2 / sys1_var, sys2_mean**2 / sys2_var]
        theta_s = [sys1_var / sys1_mean, sys2_var / sys2_mean]
        sample_size, power = find_sample_size((k_s, theta_s), alpha, desired_power, num_simulations=num_simulations, operator=operator)

        # sys1_scores = df[df['systemID'] == sys1][f'{protocol}_score']
        # sys1_scores = sys1_scores.rename(f"sys1")
        # sys1_scores.index = sys1_scores.index.map(lambda x: '#'.join(x.split("#")[:2]))
        # sys2_scores = df[df['systemID'] == sys2][f'{protocol}_score']
        # sys2_scores.index = sys2_scores.index.map(lambda x: '#'.join(x.split("#")[:2]))
        # sys2_scores = sys2_scores.rename(f"sys2")
        # sys_scores = pd.merge(sys1_scores, sys2_scores, left_index=True, right_index=True)
        # sample_size, power = find_sample_size(sys_scores, alpha, desired_power, num_simulations=num_simulations, operator=operator)

        sample_sizes.append([(sys1, sys2), sample_size])

    # store sample_sizes into json file if num_simulations is 1000
    if num_simulations == 1000:
        with open(f"{protocol}_sample_sizes.json", "w") as f:
            json.dump(sample_sizes, f)

    return calculate_sample_size_for_clusters(sample_sizes, sys_diffs)


if __name__ == '__main__':
    annotations = AnnotationLoader(refresh_cache=False)
    df = annotations.get_view(protocols=["ESA-1", "MQM-1", "WMT-MQM", "WMT-DASQM"]).dropna()

    num_simulations = 1000

    table = {}
    for protocol in ["ESA-1", "MQM-1", "WMT-MQM", "WMT-DASQM"]:
        mde = get_observable_minimum_detectable_effect(df, protocol)

        eff_clusters = effect_size_for_n_clusters(df, protocol)

        clusters = power_analysis(df, protocol, num_simulations=num_simulations)
        table[protocol] = clusters

    df = pd.DataFrame(table).sort_index()
    df.to_latex("PAPER_ESA/generated_plots/power_analysis.tex", float_format="%.0f")

    ipdb.set_trace()
