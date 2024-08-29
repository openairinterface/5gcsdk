import uuid
import requests
import httpx
from datetime import datetime
import json

#==================================================================
#                    AMF_SUBSCRIPTION                             #
#==================================================================


def get_amf_subscription_url(amf_ip, amf_port, amf_url):
    return f"http://{amf_ip}:{amf_port}{amf_url}/subscriptions"

def create_amf_subscription(sub_endpoint , ip_addr, port, event , http_version):
    if http_version == 2 : 
        http_2=True 
        http_1=False
    if http_version == 1 : 
        http_2=False  
        http_1=True    
    sub_body = json.dumps({
        "subscription": {
            "eventList": [{"type": event}],
            "eventNotifyUri": f"{ip_addr}:{port}/callbacks/amf-reports",
            "notifyCorrelationId": str(uuid.uuid1()),
            "nfId": str(uuid.uuid1())
        }
    }
    )
    try:
        with httpx.Client(http2=http_2, http1=http_1) as client:
            r = client.post(sub_endpoint, data=sub_body )
            print(r.text)
            if(r.status_code == 201):
                loc = r.headers['Location']
                start_pos = loc.find("/subscriptions/")
                loc = f"{sub_endpoint}{loc[start_pos+len('/subscriptions/')]} " 
                return loc
            else:
                return ""
    except Exception as e:
        return ""



#==================================================================
#                    SMF_SUBSCRIPTION                             #
#==================================================================


def get_smf_subscription_url(smf_ip, smf_port, smf_url):
     return f"http://{smf_ip}:{smf_port}{smf_url}/subscriptions"

def create_smf_subscription(sub_endpoint , ip_addr, port, event , http_version):
    if http_version == 2 : 
        http_2=True 
        http_1=False
    if http_version == 1 : 
        http_2=False  
        http_1=True
    sub_body = json.dumps({
        "anyUeInd": True,
        "groupId": "aEb1CD9b-561-97-2cbA7bEc2eAC07ECb6",
        "pduSeId": 1,
        "dnn": "oai",
        "notifId": str(uuid.uuid1()),
        "notifUri": f"{ip_addr}:{port}/callbacks/dataplane-reports",
        "altNotifIpv4Addrs": [ip_addr],
        "altNotifIpv6Addrs": ["fe80::14e0:6d4a:928e:628c"],
        "altNotifFqdns": ["string"],
        "eventSubs": [{"event": event}],
        "eventNotifs": [{"event": event, "timeStamp": str(datetime.utcnow().isoformat()[:-3])+'Z'}]
    }
    )
    try:
        with httpx.Client(http2=http_2, http1=http_1) as client:
            r = client.post(sub_endpoint, data=sub_body )
            print(r.text)
            if(r.status_code == 201):
                loc = r.headers['Location']
                start_pos = loc.find("/subscriptions/")
                loc = f"{sub_endpoint}{loc[start_pos+len('/subscriptions/')]} " 
                return loc
            else:
                return ""
    except Exception as e:
        print('error', e)
        return ""


#==================================================================
#                    NETWORK_PERFORMANCE_SUBSCRIPTION             #
#==================================================================


def get_network_performance_subscription_url(nwdaf_name, nwdaf_url) :
    sub_endpoint = f"http://{nwdaf_name}{nwdaf_url}/subscriptions"
    return     sub_endpoint 

def create_network_performance_subscription(sub_endpoint, sbi_ip , sbi_port , nwdaf_url):


    sub_body = {
        "notificationURI": f"http://{sbi_ip}:{sbi_port}/network_performance_notification",
        "eventSubscriptions": [
            {
                "event": "NETWORK_PERFORMANCE",
                "extraReportReq": {
                    "startTs": "2023-03-03T16:58:51.618Z",
                    "endTs": "2025-02-27T14:10:51.618Z",
                    "anaMetaInd": {
                        "dataWindow": {
                            "startTime": "2023-02-27T14:10:51.618Z",
                            "stopTime": "2023-02-27T14:10:51.618Z"
                        }
                    }
                },
                "loadLevelThreshold": 0,
                "notificationMethod": "PERIODIC",
                "repetitionPeriod": 4,
                "nwPerfRequs": [
                    {
                        "nwPerfType": "NUM_OF_UE"
                    },
                    {
                        "nwPerfType": "SESS_SUCC_RATIO"
                    }
                ]
            },
            {
                "event": "UE_COMMUNICATION",
                "extraReportReq": {
                    "startTs": "2023-03-03T16:58:51.618Z",
                    "endTs": "2025-02-27T14:10:51.618Z",
                    "anaMetaInd": {
                        "dataWindow": {
                            "startTime": "2023-02-27T14:10:51.618Z",
                            "stopTime": "2023-02-27T14:10:51.618Z"
                        }
                    }
                },
                "loadLevelThreshold": 0,
                "notificationMethod": "PERIODIC",
                "repetitionPeriod": 4
            }
        ]
    }

    try:
        r = requests.post(sub_endpoint, json=sub_body)
        print(r.status_code)

        if(r.status_code == 201):
            loc = r.headers['Location']
            locs = loc.split(f"{nwdaf_url}/subscriptions/")
            loc = f"{sub_endpoint}/{locs[1]}"
            return loc
        else:
            return ""
    except:
        return ""


#==================================================================
#                    ANOMALY_SUBSCRIPTION                          #
#==================================================================


def get_anomaly_subscription_url(nwdaf_name, nwdaf_url):
    sub_endpoint = f"http://{nwdaf_name}{nwdaf_url}/subscriptions"
    return sub_endpoint

def create_anomaly_subscription(sbi_ip , sbi_port , sub_endpoint ,nwdaf_url ):

    sub_body = {
        "notificationURI":  f"http://{sbi_ip}:{sbi_port}/anomaly_notification",
        "eventSubscriptions": [
            {
                "event": "ABNORMAL_BEHAVIOUR",
                "excepRequs": [
                    {
                        "excepId": "UNEXPECTED_LARGE_RATE_FLOW"
                    }
                ],
                "notificationMethod": "PERIODIC",
                "repetitionPeriod": 10
            }
        ]
    }

    try:
        r = requests.post(sub_endpoint, json=sub_body)
        print(r.status_code)

        if(r.status_code == 201):

            loc = r.headers['Location']
            locs = loc.split(f"{nwdaf_url}/subscriptions/")
            loc = f"{sub_endpoint}/{locs[1]}"
            return loc
        else:
            return ""
    except:
        return ""
    

#==================================================================
#                    TRACK_UE_SUBSCRIPTION                         #
#==================================================================


def get_track_ue_location_url(nwdaf_name , nwdaf_url):
    sub_endpoint = f"http://{nwdaf_name}{nwdaf_url}/subscriptions"
    return sub_endpoint

def create_track_ue_location(sbi_ip, sbi_port, sub_endpoint, nwdaf_url ):

    sub_body = {
        'notificationURI': f"http://{sbi_ip}:{sbi_port}/notification",
        'eventSubscriptions': [
            {
                'event': 'UE_MOBILITY',
                'notificationMethod': 'PERIODIC',
                'repetitionPeriod': 3,
                'tgtUe': {
                    'supis': ['imsi-208950000000031']
                }
            }
        ]
    }

    try:
        r = requests.post(sub_endpoint, json=sub_body)
        print(r.status_code)

        if(r.status_code == 201):
            loc = r.headers['Location']
            locs = loc.split(f"{nwdaf_url}/subscriptions/")
            loc = f"{sub_endpoint}/{locs[1]}"
            return loc
        else:
            return ""
    except:
       return ""