import uuid
import requests
from datetime import datetime

def get_amf_subscription_url(amf_ip, amf_port, amf_url):
    return f"http://{amf_ip}:{amf_port}{amf_url}/subscriptions"

def create_amf_subscription(sub_endpoint , ip_addr, port):
    sub_body = {
        "subscription": {
            "eventList": [{"type": "REGISTRATION_STATE_REPORT"}],
            "eventNotifyUri": f"{ip_addr}:{port}/callbacks/amf-reports",
            "notifyCorrelationId": str(uuid.uuid1()),
            "nfId": str(uuid.uuid1())
        }
    }
    try:
        r = requests.post(url=sub_endpoint, json=sub_body)
        if r.status_code == 201:
            loc = r.headers['Location']
            locs = loc.split("namf-evts/")
            return sub_endpoint+"/"+ locs[2]
        else:
            return ""
    except:
        return ""
def get_smf_subscription_url(smf_ip, smf_port, smf_url):
     return f"http://{smf_ip}:{smf_port}{smf_url}/subscriptions"

def create_smf_subscription(sub_endpoint , ip_addr, port):
    sub_body = {
        "anyUeInd": True,
        "groupId": "aEb1CD9b-561-97-2cbA7bEc2eAC07ECb6",
        "pduSeId": 1,
        "dnn": "oai",
        "notifId": str(uuid.uuid1()),
        "notifUri": f"{ip_addr}:{port}/callbacks/dataplane-reports",
        "altNotifIpv4Addrs": [ip_addr],
        "altNotifIpv6Addrs": ["fe80::14e0:6d4a:928e:628c"],
        "altNotifFqdns": ["string"],
        "eventSubs": [{"event": "PDU_SES_EST"}],
        "eventNotifs": [{"event": "PDU_SES_EST", "timeStamp": str(datetime.utcnow().isoformat()[:-3])+'Z'}]
    }
    try:
        r = requests.post(url=sub_endpoint, json=sub_body)
        if r.status_code == 201:
            loc = r.headers['Location']
            locs = loc.split("nsmf_event-exposure/")
            return sub_endpoint+"/"+locs[2]
        else:
            return ""
    except:
        return ""
