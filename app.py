import flask
from flask import request, jsonify
import socket   
import json
import requests
import signal 
from utils.config import configuration as config
from utils.subscriptions import createSmfSubscription, createAmfSubscription
import logging
from models.ue import UE
import time
from pymongo import MongoClient
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ues = {}
ues_ngapid = {}
subs = {}


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

def clean_collections():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']

    amf_collection = db['amf_notifications']
    amf_collection.delete_many({})

    smf_collection = db['smf_notifications']
    smf_collection.delete_many({})

    log.info("Collections cleaned.")

clean_collections() 


######################## INIT SUBSCRIPTIONS TO CN ############################
log.info(f"Subscribing to Registration Events from AMF")
amf_sub = createAmfSubscription()
log.info(f"Subscribing to User Sessions Events from SMF")
smf_sub = createSmfSubscription()
if amf_sub == "" or smf_sub == "":
    log.error("Subscription to CN events failed... Exiting")
    exit(1)


app = flask.Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

client = MongoClient('mongodb://localhost:27017/')
db = client['notification_db']
amf_collection = db['amf_notifications']
smf_collection = db['smf_notifications']

@app.route('/callbacks/amf-reports', methods=[ 'POST'])
def receive_amf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info(content)
        amf_collection.insert_one(content) 
        for report in content["reportList"]:
            if report["type"] == "REGISTRATION_STATE_REPORT":
                for rmInfo in report["rmInfoList"]:
                    if rmInfo["rmState"] == "REGISTERED":
                        if report["supi"] not in ues.keys():
                            ue = UE(report["supi"],report["ranUeNgapId"])
                            ues[report["supi"]] = ue
                            ues_ngapid[str(report["ranUeNgapId"])] = report["supi"]

                        else:
                            ues[report["supi"]].update_ngap_id(report["ranUeNgapId"])

                    elif rmInfo["rmState"] == "DEREGISTERED":
                        if report["supi"] in ues.keys():
                            ues.pop(report["supi"])

    
    return "OK"



@app.route('/callbacks/dataplane-reports', methods=[ 'POST'])
def receive_smf_notification():
    if request.method == 'POST':
        # get UE IMSI
        content = request.get_json(force=True)
        log.info(content)
        smf_collection.insert_one(content)
        for event in content["eventNotifs"]:
            if event["event"] == "PDU_SES_EST":
                if f"imsi-{event['supi']}" not in ues.keys():
                    ues[f"imsi-{event['supi']}"] = UE(f"imsi-{event['supi']}", "")
                ues[f"imsi-{event['supi']}"].append_ip(event['adIpv4Addr'])

    return "OK"


@app.route('/ue_identity/v1/<ue_id>', methods=['GET'])
def get_identity(ue_id):
    if request.method == 'GET':
        if validate_ip(ue_id):
            for ue in ues.values():
                if ue.has_ip(str(ue_id)):
                    return jsonify(ue.to_http_response(ue_id)) 
        else:
            log.info("###############")
            log.info(ues_ngapid)
            if ue_id in ues_ngapid.keys():
                imsi = ues_ngapid[str(ue_id)]
                #print(ues)
                ue = ues[imsi]
                #print(ue)
                res = ue.to_http_response(ue_id)
                log.info(res)
                return jsonify(res)
        return "Not found", 404
    return "Bad request", 400

@app.route('/dashboard', methods=['GET'])
def dashboard():
    	
    return "<h1> Network Monitoring Dashboard</h1> " + str(ues)

app.config["DEBUG"] = False
app.run(host=config['sbi']['ip'], port=config['sbi']['port'])






#================= terminator ====================
# Deletes subscriptions when the process is killed

def terminator(signum, frame, ask=True):
    print("Terminating...")
    if amf_sub != "":    
        url = amf_sub
        print(requests.delete(url).status_code)
    if smf_sub != "":    
        url = smf_sub
        print(requests.delete(url).status_code)

#signal.signal(signal.SIGKILL, terminator)
signal.signal(signal.SIGTERM, terminator)
signal.signal(signal.SIGINT, terminator)
signal.pause()


