import scipy.stats
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import ESA.figutils
import ipdb
from ESA.utils import PROTOCOL_DEFINITIONS


def overlaps(error, error2):
    if "start" in error2:
        error2['start_i'] = error2['start']
        error2['end_i'] = error2['end']

    if error['start_i'] == "missing":
        error['is_source_error'] = True
    if error2['start_i'] == "missing":
        error2['is_source_error'] = True

    if "is_source_error" not in error:
        error['is_source_error'] = False
    if "is_source_error" not in error2:
        error2['is_source_error'] = False

    if error['is_source_error'] and error2['is_source_error']:
        return True
    if error['is_source_error'] or error2['is_source_error']:
        return False

    start = int(error['start_i'])
    end = int(error['end_i'])
    start2 = int(error2['start_i'])
    end2 = int(error2['end_i'])
    return start2 <= start <= end2 or start2 <= end <= end2


def category_matches(error, error2, with_subcategory=True):
    if "error_type" in error and "error_type" in error2:
        # Appraise comparison
        if with_subcategory:
            return error['error_type'] == error2['error_type']
        else:
            return error['error_type'][0] == error2['error_type'][0]

    if with_subcategory:
        return False

    # WMT-MQM can be compared only on main categories
    error1_cat = error['error_type'][0].lower()
    error2_cat = error2['category'].split("/")[0].lower()

    return error1_cat == error2_cat


def severity_matches(error, error2):
    return error['severity'] == error2['severity']


def mqm_categories(df, protocol1, protocol2):
    subdf = df[[f'{protocol1}_error_spans', f'{protocol2}_error_spans']].dropna()
    total = 0
    agreed_subcategories = 0
    overlapping_subcategories = 0
    overlapping_severity_subcategories = 0

    agreed_categories = 0
    overlapping_categories = 0
    overlapping_severity_categories = 0

    overlapping_errors = 0
    overlapping_severities = 0

    for index, row in subdf.iterrows():
        for error in row[f'{protocol1}_error_spans']:
            total += 1

            found_subcategory = False
            found_subcategory_overlap = False
            found_overlap_severity_subcategory = False

            found_category = False
            found_category_overlap = False
            found_overlap_severity_category = False

            found_overlap = False
            found_overlap_severity = False
            for error2 in row[f'{protocol2}_error_spans']:
                if category_matches(error, error2):
                    found_subcategory = True
                    if overlaps(error, error2):
                        found_subcategory_overlap = True
                        if severity_matches(error, error2):
                            found_overlap_severity_subcategory = True

                if category_matches(error, error2, with_subcategory=False):
                    found_category = True
                    if overlaps(error, error2):
                        found_category_overlap = True
                        if severity_matches(error, error2):
                            found_overlap_severity_category = True

                if overlaps(error, error2):
                    found_overlap = True
                    if severity_matches(error, error2):
                        found_overlap_severity = True

            if found_subcategory:
                agreed_subcategories += 1
            if found_subcategory_overlap:
                overlapping_subcategories += 1
            if found_overlap_severity_subcategory:
                overlapping_severity_subcategories += 1

            if found_category:
                agreed_categories += 1
            if found_category_overlap:
                overlapping_categories += 1
            if found_overlap_severity_category:
                overlapping_severity_categories += 1

            if found_overlap:
                overlapping_errors += 1
            if found_overlap_severity:
                overlapping_severities += 1

    return {
        # "# Errors": total,
        "Any errors": f"{100*overlapping_errors/total:.1f}\%",
        "Same severity": f"{100*overlapping_severities/total:.1f}\%",
        "Same category": f"{100*overlapping_categories/total:.1f}\%",
        "Same sev. + categ.": f"{100*overlapping_severity_categories/total:.1f}\%",
        "Same sev. + subcateg.": (f"{100*overlapping_severity_subcategories/total:.1f}\%" if protocol2 != "WMT-MQM" else "-")

    }
    # return {
    #     "error_count": total,
    #     "overlap_agreement": 100*overlapping_errors/total,
    #     "overlap_severity_agreement": 100*overlapping_severities/total,
    #     "subcategory_agreement": 100*agreed_subcategories/total,
    #     "overlap_subcategory_agreement": 100*overlapping_subcategories/total,
    #     "overlap_severity_subcategory_agreement": 100*overlapping_severity_subcategories/total,
    #     "category_agreement": 100*agreed_categories/total,
    #     "overlap_category_agreement": 100*overlapping_categories/total,
    #     "overlap_severity_category_agreement": 100*overlapping_severity_categories/total,
    # }


def get_iaa(df):
    kendall = scipy.stats.kendalltau(df['score'], df['score_iaa'], variant="c")[0]
    pearson = scipy.stats.pearsonr(df['score'], df['score_iaa'])[0]
    # Next calculate how frequently does the annotator agree if there is error or there is none

    df[f'minor'] = df['error_spans'].apply(lambda x: len([xx for xx in x if xx['severity']=="minor"]) > 0)
    df[f'IAA_minor'] = df['error_spans_iaa'].apply(lambda x: len([xx for xx in x if xx['severity']=="minor"]) > 0)
    df[f'major'] = df['error_spans'].apply(lambda x: len([xx for xx in x if xx['severity']=="major"]) > 0)
    df[f'IAA_major'] = df['error_spans_iaa'].apply(lambda x: len([xx for xx in x if xx['severity']=="major"]) > 0)
    df['error_spans'] = df['error_spans'].apply(lambda x: len(x) > 0)
    df['error_spans_iaa'] = df['error_spans_iaa'].apply(lambda x: len(x) > 0)

    agree = (df['error_spans'] == df['error_spans_iaa']).sum()
    agreemin = (df[f'minor'] == df[f'IAA_minor']).sum()
    agreemaj = (df[f'major'] == df[f'IAA_major']).sum()

    recall = 100*agree/len(df)
    recallmin = 100*agreemin/len(df)
    recallmaj = 100*agreemaj/len(df)

    return kendall, pearson, recall, recallmin, recallmaj


def get_df_scores(df, protocoltype, iaa_type):
    protocol = protocoltype.replace("-mqm", "")
    if iaa_type == "Intra AA":
        iaa_protocol = f"{protocol}-IAA"
    else:
        if protocol == "MQM":
            iaa_protocol = "WMT-MQM"
        else:
            iaa_protocol = f"{protocol}-2"
    if protocol.endswith("-mqm"):
        subdf = df[[
            f'{protocol}-1_score_mqm',
            f'{iaa_protocol}_score_mqm',
            f'{protocol}-1_error_spans',
            f'{iaa_protocol}_error_spans',
        ]].dropna()
    else:
        subdf = df[[f'{protocol}-1_score',
                    f'{iaa_protocol}_score',
                    f'{protocol}-1_error_spans',
                    f'{iaa_protocol}_error_spans']].dropna()

    # rename columns to score vs score_iaa
    subdf.columns = [f'score', f'score_iaa', f'error_spans', f'error_spans_iaa']
    return subdf


def plot_confusion_plot(df, protocols):
    columns = len(protocols)

    fig, axs = plt.subplots(1, columns, figsize=(2.3 * columns, 2.3))
    axs = axs.flatten()
    scores = {}
    for iaa in ["Intra AA", "Inter AA"]:
        for i, protocoltype in enumerate(protocols):
            protocolname = protocoltype
            scores[(iaa, protocolname)] = {}

            subdf = get_df_scores(df, protocoltype, iaa)

            kendall, pearson, recall, recall_minor, recall_major = get_iaa(subdf)

            scores[(iaa, protocolname)]["Kendall's Tau-c"] = f"{kendall:.3f}"
            scores[(iaa, protocolname)]["Pearson"] = f"{pearson:.3f}"
            scores[(iaa, protocolname)]["Error recall"] = f"{recall:.1f}\%"
            scores[(iaa, protocolname)]["Minor e. recall"] = f"{recall_minor:.1f}\%"
            scores[(iaa, protocolname)]["Major e. recall"] = f"{recall_major:.1f}\%"

            if iaa == "Inter AA":
                continue

            subdf.plot.scatter(x=f'score', y=f'score_iaa', ax=axs[i], color="black", s=1)
            # axs[i].set_xlabel("")
            axs[i].set_ylabel("")
            axs[i].set_xlabel(protocolname.replace("ESAAI", r"ESA$^\mathrm{AI}$"))

            axs[i].add_patch(
                Rectangle(
                    (0.04, 0.05), 0.7, 0.2,
                    facecolor='#ccca',
                    fill=True,
                    linewidth=0,
                    transform=axs[i].transAxes,
                ))

            axs[i].text(0.05, 0.05, f"Kendall={kendall:.3f}\nPearson={pearson:.3f}", transform=axs[i].transAxes, ha='left', va='bottom', weight='bold')

    plt.suptitle("Intra-annotator agreement")
    plt.tight_layout(pad=0.1)
    df = pd.DataFrame(scores)

    # save the plot
    if "ESAAI" in protocols:
        plt.savefig("PAPER_ESAAI/generated_plots/intra_annotator_agreement.pdf")
        df.to_latex("PAPER_ESAAI/generated_plots/intra_annotator_agreement.tex", escape=False, multicolumn=True, column_format="l|ll|ll")
    else:
        plt.savefig("PAPER_ESA/generated_plots/intra_annotator_agreement.pdf")
        df.to_latex("PAPER_ESA/generated_plots/intra_annotator_agreement.tex", escape=False, multicolumn=True, column_format="l|ll|ll")
    plt.show()


def IntraAnnotatorAgreement(annotations):
    ESA.figutils.matplotlib_default()
    df = annotations.get_view(only_overlap=True).dropna()

    plot_confusion_plot(df, ["ESA", "MQM"])
    plot_confusion_plot(df, ["ESA", "ESAAI", "MQM"])


    a = mqm_categories(df, "MQM-1", "MQM-IAA")
    c = mqm_categories(df, "MQM-1", "WMT-MQM")

    df = pd.DataFrame([a, c], index=["Intra AA", "Inter AA"]).transpose()
    df.to_latex("PAPER_ESA/generated_plots/mqm_categories.tex", escape=False)

if __name__ == "__main__":
    from ESA.annotation_loader import AnnotationLoader
    IntraAnnotatorAgreement(AnnotationLoader(refresh_cache=False))