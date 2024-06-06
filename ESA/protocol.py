from ESA.utils import load_raw_appraise_campaign, load_raw_wmt, PROTOCOL_DEFINITIONS


class Protocol:
    def __init__(self, protocol):
        assert protocol in PROTOCOL_DEFINITIONS.keys(), f"Protocol {protocol} not supported. Allowed protocols are {PROTOCOL_DEFINITIONS.keys()}."

        if PROTOCOL_DEFINITIONS[protocol]["framework"] == "appraise":
            self.df = load_raw_appraise_campaign(protocol)
        elif PROTOCOL_DEFINITIONS[protocol]["framework"] == "wmt":
            self.df = load_raw_wmt(protocol)
        else:
            raise NotImplementedError(f"Protocol {protocol} not implemented yet.")

