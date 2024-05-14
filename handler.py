import Modules.callbacks as callbacks
from Modules.UEManager import get_registered_UEs , get_changed_status_UEs
import signal
import requests
from flask import Flask, request
from pymongo import MongoClient
from subscriptions_manager.subscriptions import createSmfSubscription, createAmfSubscription , getAmfSubscriptionUrl , getSmfSubscriptionUrl
import logging
import json
import sys
import importlib
changed_status_dict={}

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['notification_db']
amf_collection = db['amf_notifications']
smf_collection = db['smf_notifications']

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Clean collections
def clean_collections():
    amf_collection.delete_many({})
    smf_collection.delete_many({})
    log.info("Collections cleaned.")

clean_collections() 

# Initialize subscriptions
log.info("Subscribing to Registration Events from AMF")
amf_endpoint =getAmfSubscriptionUrl()
print(amf_endpoint)
amf_sub = createAmfSubscription(amf_endpoint)
log.info("Subscribing to User Sessions Events from SMF")
smf_endpoint =getSmfSubscriptionUrl()
print(smf_endpoint)
smf_sub = createSmfSubscription(smf_endpoint)

if amf_sub == "" or smf_sub == "":
    log.error("Subscription to CN events failed... Exiting")
    exit(1)

#handle the callbacks for registred UEs 
def handle_registredUEscallbacks():
    with open('/home/achraf/oai_cn_sdk/Modules/events.json', 'r') as json_file:
        data = json.load(json_file)
    registered_users = get_registered_UEs()  
                
    if data["events"]["RegisteredUEs"]["callbacks"] and registered_users:
        for callback_name in data["events"]["RegisteredUEs"]["callbacks"]:
            callback_function = getattr(callbacks , callback_name, None)
            if callback_function:
                callback_function(registered_users)
                #print(registered_users)
                #callback_function(registered_users)

def handle_changedStatusCallbacks():
        global changed_status_dict
        for document in amf_collection.find():
            for report in document["reportList"]:
                supi = report["supi"]
                ran_ue_ngap_id_amf = report["ranUeNgapId"]
                rm_state_amf = report["rmInfoList"][0]["rmState"]
                print("rm state amf " , rm_state_amf)
                timestamp = report["timeStamp"]
                if supi not in changed_status_dict :
                    changed_status_dict[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                            'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

                if rm_state_amf != changed_status_dict[supi]['rmState_amf']:
                    temp_dict = {}
                    temp_dict[supi]= {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                            'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}
                    print("temp dict" , temp_dict)
                    changed_status_dict[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                            'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}
                    with open('/home/achraf/oai_cn_sdk/Modules/events.json', 'r') as json_file:
                        data = json.load(json_file)  
                    if data["events"]["UEStatus"]["callbacks"] :
                        for callback_name in data["events"]["UEStatus"]["callbacks"]:
                            callback_function = getattr(callbacks , callback_name, None)
                            if callback_function:
                                callback_function(temp_dict) 


# Route for AMF notifications
@app.route('/callbacks/amf-reports', methods=['POST'])

def receive_amf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info(content)
        amf_collection.insert_one(content) 
        importlib.reload(callbacks)
        handle_registredUEscallbacks()
        handle_changedStatusCallbacks()
                 

    return "OK"

# Route for SMF notifications
@app.route('/callbacks/dataplane-reports', methods=['POST'])
def receive_smf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info(content)
        smf_collection.insert_one(content)

    return "OK"

app.config["DEBUG"] = False
app.run(host='192.168.71.129', port=1112)
# Define termination handler
def terminator(signum, frame, ask=True):
    print("Terminating...")
    if amf_sub != "":    
        url = amf_sub
        print(requests.delete(url).status_code)
    if smf_sub != "":    
        url = smf_sub
        print(requests.delete(url).status_code)

signal.signal(signal.SIGTERM, terminator)
signal.signal(signal.SIGINT, terminator)
signal.pause()