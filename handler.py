"""
Description:
    This script sets up a Flask web application to handle AMF and SMF notifications,
    registers callback functions for various events, and updates MongoDB collections
    with received notifications.

Requirements:
    - Flask
    - pymongo
    - requests

Usage:
    - Run the script to start the Flask web application.
    - Incoming AMF notifications are handled at '/callbacks/amf-reports' endpoint.
    - Incoming SMF notifications are handled at '/callbacks/dataplane-reports' endpoint.

How to Use:
    1. Ensure all required packages are installed.
    2. Run the script.
    3. The Flask application will start, listening on the specified host and port.

"""

import Modules.callbacks as callbacks
from Modules.UEManager import get_registered_ues
import signal
import requests
from flask import Flask, request
from pymongo import MongoClient
from subscriptions_manager.subscriptions import create_smf_subscription, create_amf_subscription, get_amf_subscription_url, get_smf_subscription_url
import logging
import json
import os
import importlib
import yaml
from yaml.loader import SafeLoader


with open('configuration.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)

ip_addr = data['sbi']['ip']
port    = data['sbi']['port']

amf_addr= data['amf_1']['ip']
amf_url = data['amf_1']['url']
amf_port= data['amf_1']['port']

smf_addr= data['smf_1']['ip']
smf_url = data['smf_1']['url']
smf_port= data['smf_1']['port']


changed_status_dict = {}

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
amf_endpoint = get_amf_subscription_url(amf_addr , amf_port , amf_url)
amf_sub = create_amf_subscription(amf_endpoint , ip_addr , port)
log.info("Subscribing to User Sessions Events from SMF")
smf_endpoint = get_smf_subscription_url(smf_addr , smf_port , smf_url)
smf_sub = create_smf_subscription(smf_endpoint , ip_addr , port)

if amf_sub == "" or smf_sub == "":
    log.error("Subscription to CN events failed... Exiting")
    assert False, "Subscription to CN events failed"

# handle the callbacks for registered UEs
def handle_registered_ue_callbacks():
    home_dir = os.path.expanduser("~")
    events_json_path = os.path.join(home_dir, 'oai_cn_sdk', 'Modules', 'events.json')
    with open(events_json_path, 'r') as json_file:
        data = json.load(json_file)
    registered_users = get_registered_ues()

    if data["events"]["RegisteredUEs"]["callbacks"] and registered_users:
        for callback_name in data["events"]["RegisteredUEs"]["callbacks"]:
            callback_function = getattr(callbacks, callback_name, None)
            if callback_function:
                callback_function(registered_users)

def handle_changed_status_callbacks():
    global changed_status_dict
    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            ran_ue_ngap_id_amf = report["ranUeNgapId"]
            rm_state_amf = report["rmInfoList"][0]["rmState"]
            timestamp = report["timeStamp"]
            if supi not in changed_status_dict:
                changed_status_dict[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                              'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

            if rm_state_amf != changed_status_dict[supi]['rmState_amf']:
                temp_dict = {}
                temp_dict[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                   'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}
                changed_status_dict[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                             'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

                home_dir = os.path.expanduser("~")
                events_json_path = os.path.join(home_dir, 'oai_cn_sdk', 'Modules', 'events.json')

                with open(events_json_path, 'r') as json_file:
                    data = json.load(json_file)

                if data["events"]["UEStatus"]["callbacks"]:
                    for callback_name in data["events"]["UEStatus"]["callbacks"]:
                        callback_function = getattr(callbacks, callback_name, None)
                        if callback_function:
                            callback_function(temp_dict)


# Route for AMF notifications
@app.route('/callbacks/amf-reports', methods=['POST'])
def receive_amf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)
        amf_collection.insert_one(content)
        importlib.reload(callbacks)
        handle_registered_ue_callbacks()
        handle_changed_status_callbacks()

    return "OK"


# Route for SMF notifications
@app.route('/callbacks/dataplane-reports', methods=['POST'])
def receive_smf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)
        smf_collection.insert_one(content)

    return "OK"

app.config["DEBUG"] = False
app.run(host='192.168.71.129', port=1112)

# Define termination handler
def terminator(signum, frame, ask=True):
    log.info("Terminating...")

    if amf_sub != "":
        url = amf_sub
        response = requests.delete(url)
        log.info(f"AMF Subscription delete status code: {response.status_code}")

    if smf_sub != "":
        url = smf_sub
        response = requests.delete(url)
        log.info(f"SMF Subscription delete status code: {response.status_code}")

signal.signal(signal.SIGTERM, terminator)
signal.signal(signal.SIGINT, terminator)
signal.pause()
