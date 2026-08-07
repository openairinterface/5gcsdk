# SPDX-License-Identifier: MIT

from enum import Enum


class Metric(Enum):
    """
    Enum class for metrics, representing various attributes of a User Equipment (UE).
    
    Attributes:
    
    timestamp (str): Timestamp of the event or record.
    data_ul (str): Amount of uplink data (data sent from the UE).
    data_dl (str): Amount of downlink data (data received by the UE).
    start_interval (str): Start time of a reporting interval (input from user).
    end_interval (str): End time of a reporting interval (input from user).
    interval_size (str): Duration of the reporting interval, computed from start_interval and end_interval.
    number_pkts_ul (str): Number of uplink packets (packets sent from the UE).
    number_pkts_dl (str): Number of downlink packets (packets received by the UE).
    connectivity_status (str): Connectivity state, obtained from AMF-CONNECTIVITY_STATE_REPORT .reportList[].cmInfoList[].cmState.
    ip_address (str): IP address assigned to the UE, obtained from SMF-PDU_SES_EST .adIpv4Addr.
    imsi (str): International Mobile Subscriber Identity (IMSI) of the UE, obtained from SMF-PDU_SES_EST eventNotifs[].supi or AMF-CONNECTIVITY_STATE_REPORT .reportList[].supi.
    dnn (str): Data Network Name (DNN) associated with the UE, obtained from SMF-PDU_SES_EST eventNotifs[].dnn.
    sst (str): Slice/Service Type (SST), which can be obtained from multiple sources such as UE_COMMUNICATION .ueComms[].traffChar.snssai.sst, NDWAF-ABNORMAL_BEHAVIOUR .abnorBehavrs[].snssai.sst, or SMF-PDU_SES_EST .snssai.sst.
    sd (str): Slice Differentiator (SD), part of the S-NSSAI (Single Network Slice Selection Assistance Information).
    plmn (str): Public Land Mobile Network (PLMN) identifier.
    amf_ngap_id (str): AMF NGAP (Next Generation Application Protocol) ID.
    gnb_ngap_id (str): gNB NGAP (Next Generation Application Protocol) ID.
    cell_id (str): Cell ID, which can be obtained from NDWAF-UE_MOBILITY .ueMobs[].locInfos[].loc.
    registration_status (str): Registration status of the UE.
    """
    timestamp = 'timestamp'
    data_ul = 'data_ul'
    data_dl = 'data_dl'
    start_interval = 'start_interval'
    end_interval = 'end_interval'
    interval_size = 'interval_size'
    number_pkts_ul = 'number_pkts_ul'
    number_pkts_dl = 'number_pkts_dl'
    connectivity_status = 'connectivity_status'
    ip_address = 'ip_address'
    imsi = 'imsi'
    dnn = 'dnn'
    sst = 'sst'
    sd = 'sd'
    plmn = 'plmn'
    amf_ngap_id = 'amf_ngap_id'
    gnb_ngap_id = 'gnb_ngap_id'
    cell_id = 'cell_id'
    registration_status = 'registration_status'

            
