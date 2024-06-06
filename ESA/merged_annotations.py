raise Exception("This code uses old loader, please refactor.")
import ipdb
from ESA.settings import PROJECT
from ESA.annotations import AppraiseAnnotations, SCHEME_ESA, SCHEME_GEMBA, SCHEME_MQM, SCHEME_ESA_SEVERITY, SCHEME_GEMBA_SEVERITY, SCHEME_ESA2, SCHEME_GEMBA2


class MergedAnnotations:
    def __init__(self, second_campaign=False) -> None:
        if not second_campaign:
            schemes = [SCHEME_MQM, SCHEME_ESA]
            if PROJECT == "GEMBA":
                schemes += [SCHEME_GEMBA]
        else:
            schemes = [SCHEME_MQM, SCHEME_ESA2]
            if PROJECT == "GEMBA":
                schemes += [SCHEME_GEMBA2]

        self.annots = {}
        for scheme in schemes:
            self.annots[scheme] = AppraiseAnnotations(scheme)
            # Next code appends sources and translations to the dataframes
            self.annots[scheme].generate_wmt_score_files()

        mqm_df = self.annots[SCHEME_MQM].df
        esa_df = self.annots[schemes[1]].df
        # drop duplicated columns
        duplicated_columns = ["valid_segment", "is_bad", "source_lang", "target_lang", 'source_seg', 'translation_seg']
        esa_df = esa_df.drop(columns=duplicated_columns)

        identical_columns = ['system', 'itemID', 'documentID']
        merged = mqm_df.merge(esa_df, on=identical_columns, suffixes=('_mqm', '_esa'))

        if PROJECT == "GEMBA":
            gemba_df = self.annots[schemes[2]].df
            gemba_df = gemba_df.drop(columns=duplicated_columns)
            # add suffic to all but non-identical columns
            gemba_df.columns = [f"{col}_gemba" if col not in identical_columns else col for col in gemba_df.columns]
            merged = merged.merge(gemba_df, on=identical_columns)

        self.df = merged