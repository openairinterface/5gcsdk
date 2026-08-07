# SPDX-License-Identifier: MIT

class UE:
    def __init__(self, supi, ad_ipv4_addr, ran_ue_ngap_id, rm_state, timestamp):
        self.supi = supi
        self.ad_ipv4_addr = ad_ipv4_addr
        self.ran_ue_ngap_id = ran_ue_ngap_id
        self.rm_state = rm_state
        self.timestamp = timestamp

    def __repr__(self):
        return (f"UE(supi={self.supi}, ad_ipv4_addr={self.ad_ipv4_addr}, "
                f"ran_ue_ngap_id={self.ran_ue_ngap_id}, rm_state={self.rm_state}, "
                f"timestamp={self.timestamp})")
