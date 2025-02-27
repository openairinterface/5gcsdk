from .config import configuration as config
import uuid
import requests
from datetime import datetime

ip_addr = config['sbi']['ip']
port = config['sbi']['port']

def createAmfSubscription(event_type):    
    ### create a subscription for receiving location reports
    sub_endpoint = f"http://{config['amf']['ip']}:{config['amf']['port']}{config['amf']['baseUrl']}/subscriptions"
    print(sub_endpoint)
    print(ip_addr)
    sub_body = {
                "subscription": {
                    "eventList": [
                        {
                            "type": event_type #"REGISTRATION_STATE_REPORT"
                        }
                    ],
                    "eventNotifyUri": f"{ip_addr}:{port}/callbacks/amf-reports",
                    "notifyCorrelationId": str(uuid.uuid1()),
                    "nfId": str(uuid.uuid1())
                }
            }
    try:
        r = requests.post(url =sub_endpoint, json=sub_body)
        print(r.status_code)
        if(r.status_code == 201):
            loc = r.headers['Location']
            locs = loc.split("namf-evts/")
            loc = f"http://{config['amf']['ip']}:{config['amf']['port']}{config['amf']['baseUrl']}/subscriptions/{locs[2]}"
            return loc
        else:
            return ""
    except:
        return ""

def createSmfSubscription():    
    ### create a subscription for receiving location reports
    sub_endpoint = f"http://{config['smf']['ip']}:{config['smf']['port']}{config['smf']['baseUrl']}/subscriptions"
    sub_body ={
        "anyUeInd": True,
        "groupId": "aEb1CD9b-561-97-2cbA7bEc2eAC07ECb6",
        "pduSeId": 1,
        "dnn": "oai",
        "notifId": str(uuid.uuid1()),
        "notifUri": f"{ip_addr}:{port}/callbacks/dataplane-reports",
        "altNotifIpv4Addrs": [
            ip_addr
        ],
        "altNotifIpv6Addrs": [
            "fe80::14e0:6d4a:928e:628c"
        ],
        "altNotifFqdns": [
            "string"
        ],
        "eventSubs": [
            {
            "event": "PDU_SES_EST"
            }
        ],
        "eventNotifs": [
            {
            "event": "PDU_SES_EST",
            "timeStamp": str(datetime.utcnow().isoformat()[:-3])+'Z'
            }
        ]
    }

    sub_id = None
    try:
        r = requests.post(url =sub_endpoint, json=sub_body)
        if(r.status_code == 201):
            loc = r.headers['Location']
            locs = loc.split("nsmf_event-exposure/")
            loc = f"http://{config['smf']['ip']}:{config['smf']['port']}{config['smf']['baseUrl']}/subscriptions/{locs[2]}"
            return loc
        else:
            return ""
    except:
        return ""

