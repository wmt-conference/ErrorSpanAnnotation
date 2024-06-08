import ipdb
import pandas as pd
import matplotlib.pyplot as plt


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

    # print("#"*50)
    # print(f"Protocol {protocol1} vs {protocol2}\n")
    # print(f"{100*overlapping_errors/total:.1f}% for MQM error span overlap with ANY other (total {total} errors)")
    # print(f"{100*agreed_subcategories/total:.1f}% for MQM error category agreement with ANY (total {total} errors)")
    # print(f"{100*overlapping_categories/total:.1f}% for MQM error span overlap + category agreement (total {total} errors)")
    # print(f"{100*overlapping_severities/total:.1f}% for MQM error span overlap + severity agreement (total {total} errors)")
    # print(f"{100*overlapping_categories_severity/total:.1f}% for MQM error span overlap + severity & category agreement (total {total} errors)")
    # print("#"*50)

    return {
        "error_count": total,
        "subcategory_agreement": 100*agreed_subcategories/total,
        "overlap_subcategory_agreement": 100*overlapping_subcategories/total,
        "overlap_severity_subcategory_agreement": 100*overlapping_severity_subcategories/total,
        "category_agreement": 100*agreed_categories/total,
        "overlap_category_agreement": 100*overlapping_categories/total,
        "overlap_severity_category_agreement": 100*overlapping_severity_categories/total,
        "overlap_agreement": 100*overlapping_errors/total,
        "overlap_severity_agreement": 100*overlapping_severities/total,
    }

def plot_confusion_plot(df, protocols):
    columns = len(protocols)

    fig, axs = plt.subplots(1, columns, figsize=(2.7 * columns, 2.2 * 1))
    axs = axs.flatten()
    scores = {}
    for i, protocol in enumerate(protocols):
        scores[protocol] = {}

        subdf = df[[f'{protocol}-1_score', f'{protocol}-IAA_score']].dropna()
        # plot subdf into x-y plot, make the points smaller
        subdf.plot.scatter(x=f'{protocol}-1_score', y=f'{protocol}-IAA_score', ax=axs[i], color='darkblue', s=1)
        # do not show the axis title
        axs[i].set_xlabel("")
        axs[i].set_ylabel("")
        # print the protocol name into the plot
        axs[i].set_title(protocol)
        pearson = subdf.corr().iloc[0, 1]
        # print(f"{protocol} pearson: {pearson:.3f} on {len(subdf)} samples")
        scores[protocol]["pearson"] = pearson

        # Next calculate how frequently does the annotator agree if there is error or there is none
        subdf = df[[f'{protocol}-1_error_spans', f'{protocol}-IAA_error_spans']].dropna()
        subdf[f'{protocol}-1_error_spans'] = subdf[f'{protocol}-1_error_spans'].apply(lambda x: len(x) > 0)
        subdf[f'{protocol}-IAA_error_spans'] = subdf[f'{protocol}-IAA_error_spans'].apply(lambda x: len(x) > 0)

        agree = (subdf[f'{protocol}-1_error_spans'] == subdf[f'{protocol}-IAA_error_spans']).sum()
        # print(f"{protocol} error agreement: {agree/len(subdf):.2f} out of {len(subdf)} samples")
        recall = 100*agree/len(subdf)
        scores[protocol]["error_agreement"] = recall

        # print into the plot IAA via pearson to the bottom right corner: Intra-AA={pearson:.3f}\nError recall={recall:.1f}
        # axs[i].text(0.05, 0.05, f"Intra-AA={pearson:.3f}\nError recall={recall:.1f}%", transform=axs[i].transAxes, ha='left', va='bottom')
        # but make it bold
        axs[i].text(0.05, 0.05, f"Intra-AA={pearson:.3f}\nError recall={recall:.1f}%", transform=axs[i].transAxes, ha='left', va='bottom', weight='bold')

    # save the plot
    if "ESAAI" in protocols:
        plt.savefig("PAPER_ESAAI/generated_plots/intra_annotator_agreement.pdf")
    else:
        plt.savefig("PAPER_ESA/generated_plots/intra_annotator_agreement.pdf")



def IntraAnnotatorAgreement(annotations):
    df = annotations.get_view(only_overlap=True).dropna()

    plot_confusion_plot(df, ["MQM", "ESA"])
    plot_confusion_plot(df, ["MQM", "ESA", "ESAAI"])


    # a = mqm_categories(df, "MQM-1", "MQM-IAA")
    # b = mqm_categories(df, "MQM-IAA", "MQM-1")
    # c = mqm_categories(df, "MQM-1", "WMT-MQM")
    # d = mqm_categories(df, "MQM-IAA", "WMT-MQM")
    #
    # df = pd.DataFrame([a, b, c, d], index=["MQM-1 vs MQM-IAA", "MQM-IAA vs MQM-1", "MQM-1 vs WMT-MQM", "MQM-IAA vs WMT-MQM"])

