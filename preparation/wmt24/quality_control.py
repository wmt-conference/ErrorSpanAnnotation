import random
import copy


RANDOM_SAMPLE_BAD = random.Random(0)


def create_bad_document(data_docs, langs):
    """
    Randomly sample a document from a list and corrupt it.
    """
    all_tgt = [x["targetText"] for l in data_docs for x in l]
    character_based = langs.split("-")[1] in {"zh", "ja", "ko"}

    docs_available = [
        doc for doc in data_docs
        if "#dup" not in doc[0]["documentID"] and "#bad" not in doc[0]["documentID"]
    ]
    doc_bad = copy.deepcopy(RANDOM_SAMPLE_BAD.choice(docs_available))

    for obj in doc_bad:
        text = obj["targetText"]
        SENT_COUNT = text.count(". ") + text.count("。") + 1
        for _ in range(SENT_COUNT):
            text, start_i, end_i = corrupt_text_by_mixing(
                text,
                RANDOM_SAMPLE_BAD.choice(all_tgt),
                character_based=character_based
            )
        obj["targetText"] = text
        obj["itemType"] = "BAD"
        # no need to add a unique identifier because there's at most one bad document per good one
        obj["documentID"] = obj["documentID"] + f"#bad"

    return doc_bad


RANDOM_GEN_BAD = random.Random(0)
RANDOM_GEN_BAD_LEN = random.Random(0)


def corrupt_text_by_mixing(seg_orig: str, seg_inject: str, character_based: bool = False) -> str:
    """
    Creates bad reference for given text.

    Segment length (a, b] to phrase length (excluding a, including b)
    mapping defined as follows:
        ( 0,   1] : 1
        ( 1,   5] : 2
        ( 5,   8] : 3
        ( 8,  15] : 4
        (15,  20] : 5
        (20, max] : 6

    For character-based languages, which do not support tokenisation
    by whitespace, the resulting phrase length will be doubled, and
    is interpreted as a character length.
    """

    if character_based:
        seg_data = list(seg_orig)
        ref_data = list(seg_inject)
    else:
        seg_data = seg_orig.split(' ')
        ref_data = seg_inject.split(' ')

    seg_len = len(seg_data)
    ref_len = len(ref_data)
    bad_len = RANDOM_GEN_BAD_LEN.choice([2, 3, 4, 5, 6])

    # Double length of bad phrase for character-based languages.
    if character_based:
        bad_len = 2 * bad_len

    # Determine random replacement position. For segments longer than
    # (bad_len + 1), we enforce that this cannot be sentence initial
    # or final, so positions 0 and (seg_len - bad_len -1) are invalid
    # and we use an embedded bad_pos in [1, (seg_len - bad_len - 1)].
    # This happens for all seg_len > 3.
    bad_pos = 0
    if seg_len - bad_len > 0:
        bad_pos = RANDOM_GEN_BAD.choice(range(seg_len - bad_len))

    elif seg_len > 3:
        _xs = max(1, seg_len - bad_len - 1)
        bad_pos = RANDOM_GEN_BAD.choice([x + 1 for x in range(_xs)])

    ref_pos = 0
    if ref_len - bad_len > 0:
        ref_pos = RANDOM_GEN_BAD.choice(range(ref_len - bad_len))

    bad_data = (
        seg_data[:bad_pos]
        + ref_data[ref_pos: ref_pos + bad_len]
        + seg_data[bad_pos + bad_len:]
    )
    bad_text = ' '.join(bad_data)
    if character_based:
        bad_text = ''.join(bad_data)

    # return text but also indicies
    return (bad_text, bad_pos, bad_len)
