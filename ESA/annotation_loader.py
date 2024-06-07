import os
import ipdb
import pickle
import logging
import pandas as pd
from ESA.protocol import Protocol
from ESA.utils import PROTOCOL_DEFINITIONS
from ESA.fixed_segment_ids import FIXED_IDS


# This module is used to load the all annotations for all campaigns are return views depending on analysis
class AnnotationLoader:
    def __init__(self, refresh_cache):
        self.protocols = {}
        self._load_cache(refresh_cache)

    def _load_cache(self, refresh_cache):
        cache_file = 'cache_protocols_v2.pkl'  # using versioning to force change everywhere if coded is changed
        if refresh_cache or not os.path.exists(cache_file):
            self.protocols = {}
            for protocol in PROTOCOL_DEFINITIONS:
                self._get_protocol_data(protocol)

            # save protocols into pickle
            with open(cache_file, 'wb') as f:
                pickle.dump(self.protocols, f)

        else:
            with open(cache_file, 'rb') as f:
                self.protocols = pickle.load(f)

    def _get_protocol_data(self, protocol):
        if protocol not in self.protocols:
            self.protocols[protocol] = Protocol(protocol)

        return self.protocols[protocol]

    def get_view(self, protocols=None, only_overlap=True):
        if protocols is None:
            protocols = PROTOCOL_DEFINITIONS.keys()

        generic_columns = ['domainID', 'documentID', 'source', 'hypothesis', 'systemID', 'sourceID', 'hypothesisID']
        unique_columns = ['score', 'login', 'is_bad', 'start_time', 'end_time', 'error_spans', 'duration_seconds', 'AnnotatorID']

        columns_descriptions = {
               'login': 'Appraise login unique for each HIT',
               'systemID': 'System ID which produced hypothesis',
               'is_bad': 'Quality control - TGT for valid hypotheses, BAD for quality control items',
               'score': 'Assigned score for given segment as defined by protocol',
               'documentID': 'Unique document ID for each document in the WMT dataset',
               'span_errors': 'Assigned errors for given segment as defined by protocol - only for MQM, ESA, ESAAI',
               'start_time': 'Appraise start time without any filtering',
               'end_time': 'Appraise end time without any filtering',
               'duration_seconds': 'How long did it take to annotate the segment in seconds, after filtering',
               'AnnotatorID': 'Unique ID for each human annotator',
               }

        dfs = None
        for protocol in protocols:
            df = self._get_protocol_data(protocol).df.copy()
            # append protocol name to columns except for generic columns
            df.columns = [f"{protocol}_{col}" if col not in generic_columns else col for col in df.columns]
            if dfs is None:
                dfs = df
            else:
                df = df.drop(columns=generic_columns)
                dfs = dfs.merge(df, how='outer', left_index=True, right_index=True)

        if only_overlap:
            # keep only FIXED_IDS in the view
            dfs = dfs[dfs.index.isin(FIXED_IDS)]
        return dfs
