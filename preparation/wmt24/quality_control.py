import random
import copy


RANDOM_SAMPLE_BAD = random.Random(0)


def create_bad_document(data_docs):
    """
    Randomly sample a document from a list and corrupt it.
    """
    all_tgt = [x["targetText"] for l in data_docs for x in l]

    docs_available = [
        doc for doc in data_docs
        if "#dup" not in doc[0]["documentID"] and "#bad" not in doc[0]["documentID"]
    ]
    doc_bad = copy.deepcopy(RANDOM_SAMPLE_BAD.choice(docs_available))

    for obj in doc_bad:
        sents = []
        for sent in obj["targetText"].split(". "):
            # don't corrupt if it's short sentence (could be a non-sentences)
            if len(sent.split()) < 5:
                sents.append(sent)
            else:
                corrupted, start_i, end_i = corrupt_text_by_mixing(
                    obj["targetText"],
                    RANDOM_SAMPLE_BAD.choice(all_tgt),
                    character_based=False
                )
                sents.append(corrupted)
        obj["targetText"] = ". ".join(sents)
        obj["itemType"] = "BAD"
        # no need to add a unique identifier because there's at most one bad document per good one
        obj["documentID"] = obj["documentID"] + f"#bad"

    return doc_bad


RANDOM_GEN_BAD = random.Random(0)


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

    # Determine length of bad phrase, relative to segment length.
    _seg_to_bad_mapping = {
        (None, 1): 2,
        (1, 5): 2,
        (5, 8): 3,
        (8, 15): 4,
        (15, 20): 5,
        (20, None): 6,
    }

    bad_len = 0
    for seg_pair in _seg_to_bad_mapping:
        left, right = seg_pair

        # seg_len == right; left edge case
        if not left:
            if seg_len == right:
                bad_len = _seg_to_bad_mapping[seg_pair]
                break

        # left < seg_len; right edge case
        elif not right:
            if left < seg_len:
                bad_len = _seg_to_bad_mapping[seg_pair]
                break

        # left < seg_len <= right; middle cases
        elif left < seg_len <= right:
            bad_len = _seg_to_bad_mapping[seg_pair]
            break

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
