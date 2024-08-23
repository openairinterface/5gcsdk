class UE:
    def __init__(self, supi, ad_ipv4_addr, ran_ue_ngap_id, rm_state, timestamp , amf_ngap_id='', plmn='',cell_id='', sd='',sst='', dnn='', number_pkts_dl='',number_pkts_ul='', data_ul='', data_dl='' ):
        self.supi = supi
        self.ad_ipv4_addr = ad_ipv4_addr
        self.ran_ue_ngap_id = ran_ue_ngap_id
        self.rm_state = rm_state
        self.timestamp = timestamp
        self.data_ul = data_ul
        self.data_dl = data_dl
        self.number_pkts_ul = number_pkts_ul
        self.number_pkts_dl = number_pkts_dl
        self.dnn = dnn
        self.sst = sst
        self.sd = sd
        self.plmn = plmn
        self.amf_ngap_id = amf_ngap_id
        self.cell_id = cell_id


    def __repr__(self):
        attributes = []
        if self.supi: attributes.append(f"supi={self.supi}")
        if self.ad_ipv4_addr: attributes.append(f"ad_ipv4_addr={self.ad_ipv4_addr}")
        if self.ran_ue_ngap_id: attributes.append(f"ran_ue_ngap_id={self.ran_ue_ngap_id}")
        if self.rm_state: attributes.append(f"rm_state={self.rm_state}")
        if self.timestamp: attributes.append(f"timestamp={self.timestamp}")
        if self.data_ul: attributes.append(f"data_ul={self.data_ul}")
        if self.data_dl: attributes.append(f"data_dl={self.data_dl}")
        if self.number_pkts_ul: attributes.append(f"number_pkts_ul={self.number_pkts_ul}")
        if self.number_pkts_dl: attributes.append(f"number_pkts_dl={self.number_pkts_dl}")
        if self.dnn: attributes.append(f"dnn={self.dnn}")
        if self.sst: attributes.append(f"sst={self.sst}")
        if self.sd: attributes.append(f"sd={self.sd}")
        if self.plmn: attributes.append(f"plmn={self.plmn}")
        if self.amf_ngap_id: attributes.append(f"amf_ngap_id={self.amf_ngap_id}")
        if self.cell_id: attributes.append(f"cell_id={self.cell_id}")
        
        return f"UE({', '.join(attributes)})"
