import random

LANG_2_TO_3 = {
    "en": "eng",
    "de": "deu",
    "cs": "ces",
    "hr": "hrv",
    "pl": "plk",
    "ru": "rus",
    "zh": "zho",
}

RANDOM_SAMPLE_BAD = random.Random(0)
def sample_bad_documents(data_bad, bad_segments):
    import copy
    import collections

    data_docs = collections.defaultdict(list)
    all_tgt = []
    for obj in data_bad:
        data_docs[obj["documentID"]].append(obj)
        all_tgt.append(obj["targetText"])
    data_docs = list(data_docs.values())

    docs = []
    while bad_segments != 0:
        available = [doc_i for doc_i, doc in enumerate(data_docs) if len(doc) <= bad_segments]

        if not data_docs:
            # clip last one
            docs.append(copy.deepcopy(RANDOM_SAMPLE_BAD.choice(docs))[:bad_segments])
            bad_segments -= len(docs[-1])
        elif not available:
            # clip last one
            doc_i = RANDOM_SAMPLE_BAD.choice(range(len(data_docs)))
            docs.append(data_docs.pop(doc_i)[:bad_segments])
            bad_segments = 0
        else:
            doc_i = RANDOM_SAMPLE_BAD.choice(available)
            docs.append(data_docs.pop(doc_i))
            bad_segments -= len(docs[-1])
    
    
    docs = copy.deepcopy(docs)
    for doc_i, doc in enumerate(docs):
        for obj in doc:
            corrupted, start_i, end_i = corrupt_text_by_mixing(
                obj["targetText"],
                RANDOM_SAMPLE_BAD.choice(all_tgt),
                character_based=False
            )
            obj["targetText"] = corrupted
            # obj["itemType"] = f"BAD.{start_i}.{end_i}"
            obj["itemType"] = "BAD"
            obj["documentID"] = obj["documentID"] + f"#bad{doc_i+1}"

    docs = [x for doc in docs for x in doc]
    return docs

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
        + ref_data[ref_pos : ref_pos + bad_len]
        + seg_data[bad_pos + bad_len :]
    )
    bad_text = ' '.join(bad_data)
    if character_based:
        bad_text = ''.join(bad_data)

    # return text but also indicies
    return (bad_text, bad_pos, bad_len)
