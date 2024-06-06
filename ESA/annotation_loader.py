import ipdb
import logging
from ESA.protocol import Protocol


# This module is used to load the all annotations for all campaigns are return views depending on analysis
class AnnotationLoader:
    def __init__(self):
        self.protocols = {}

    def _get_protocol_data(self, protocol):
        if protocol not in self.protocols:
            self.protocols[protocol] = Protocol(protocol)

        return self.protocols[protocol]

    def get_view(self, protocols, columns=None):
        all_columns = {'login': 'Appraise login unique for each HIT',
                       'systemID': 'System ID which produced hypothesis',  # TODO may not be needed
                       'itemID': 'Appraise ID referring to items in a HIT',  # TODO may not be needed
                       'is_bad': 'Quality control - TGT for valid hypotheses, BAD for quality control items',
                       'source_lang': 'Source language, in our setup always English',  # TODO may not be needed
                       'target_lang': 'Target language, in our setup always German',  # TODO may not be needed
                       'score': 'Assigned score for given segment as defined by protocol',
                       'documentID': 'Unique document ID for each document in the WMT dataset', # TODO may not be needed, instead we should have hypothesisID
                       'span_errors': 'Assigned errors for given segment as defined by protocol - only for MQM, ESA, ESAAI',
                       'start_time': 'Appraise start time without any filtering',
                       'end_time': 'Appraise end time without any filtering',
                       'duration_seconds': 'How long did it take to annotate the segment in seconds, after filtering',
                       'AnnotatorID': 'Unique ID for each human annotator',
                       # 'valid_segment': 'Filters out BAD and tutorial segments'
                       }

        if columns is None:
            columns = all_columns.keys()
            info = ""
            for col in columns:
                info += f"{col}: {all_columns[col]}\n"
            logging.info(f"Available columns:\n{info}")

        p = {}
        for protocol in protocols:
            p[protocol] = self._get_protocol_data(protocol)

        ipdb.set_trace()