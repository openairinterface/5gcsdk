import uuid
import requests
from datetime import datetime

def createAmfSubscription(ip_addr='192.168.71.129', port=1112, amf_ip='192.168.71.132', amf_port=80, amf_url='/namf-evts/v1'):
    sub_endpoint = f"http://{amf_ip}:{amf_port}{amf_url}/subscriptions"
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
            return f"http://{amf_ip}:{amf_port}{amf_url}/subscriptions/{locs[2]}"
        else:
            return ""
    except:
        return ""

def createSmfSubscription(ip_addr='192.168.71.129', port=1112, smf_ip='192.168.71.133', smf_port=80, smf_url='/nsmf_event-exposure/v1'):
    sub_endpoint = f"http://{smf_ip}:{smf_port}{smf_url}/subscriptions"
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
            return f"http://{smf_ip}:{smf_port}{smf_url}/subscriptions/{locs[2]}"
        else:
            return ""
    except:
        return ""
