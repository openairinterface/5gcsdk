# SPDX-License-Identifier: MIT

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
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'modules'))
sys.path.append(os.path.join(parent_dir, 'subscriptions_manager'))
from data_models.Metric import Metric
import callbacks as callbacks
import signal
import threading
import time
import requests
import subprocess
from flask import Flask, request , jsonify
from pymongo import MongoClient , errors
import subscriptions as subscriptions
import logging
import json
import importlib
import yaml
from yaml.loader import SafeLoader

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
config_file_path = os.path.join(parent_dir, 'etc', 'configuration.yaml')
status_file_path = os.path.join(current_dir, '../../etc/handler_status.yaml')

with open(config_file_path, 'r') as f:
    data = yaml.load(f, Loader=SafeLoader)

sbi_addr  = data['sbi']['ip']
sbi_port  = data['sbi']['port']

amf_addr  = data['amf_1']['ip']
amf_url   = data['amf_1']['url']
amf_port  = data['amf_1']['port']

smf_addr  = data['smf_1']['ip']
smf_url   = data['smf_1']['url']
smf_port  = data['smf_1']['port']

nwdaf_name= data['nwdaf-sbi']['name']
nwdaf_url =  data['nwdaf-sbi']['url']


changed_status_dict = {}

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger("docker.utils.config").setLevel(logging.WARN)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARN)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)




try:
    client = MongoClient('mongodb://localhost:27017/')
    # Attempt to fetch server information to check connection
    client.server_info()
except errors.ServerSelectionTimeoutError:
    with open(status_file_path, 'r') as file:
        data = yaml.safe_load(file)
    data['handler_status'] = 'off'
    data['handler_pid'] = 'None'
    with open(status_file_path, 'w') as file:
        yaml.safe_dump(data, file)
    raise AssertionError("Failed to connect to MongoDB")

db = client['notification_db']
amf_collection = db['amf_notifications']
amf_location_collection=db['amf_location_notification']
smf_collection = db['smf_notifications']
smf_traffic_collection = db['smf_notification_traffic']
nwdaf_location_collection= db['nwdaf_location_traffic']

log.info("Successfully connected to MongoDB.")




# Initialize MongoDB collections


# Clean collections
def clean_collections():
    amf_collection.delete_many({})
    smf_collection.delete_many({})
    smf_traffic_collection.delete_many({})
    amf_location_collection.delete_many({})
    nwdaf_location_collection.delete_many({})
    log.info("Collections cleaned.")
    
clean_collections()

# Subscription URLs, filled in as each subscription is created; "" means not subscribed.
amf_sub = amf_sub_location = smf_sub = smf_sub_qos_mon = ""
net_per_sub = anomaly_sub = track_ue_sub = ""

# Define termination handler
# Deletions run in parallel and must all finish within this budget, which has to stay
# below the 5 s stop_handler() waits before it kills the handler.
SHUTDOWN_DEADLINE = 3

def delete_subscription(name, url):
    try:
        response = requests.delete(url, timeout=SHUTDOWN_DEADLINE)
        log.info(f"{name} subscription delete status code: {response.status_code}")
    except requests.RequestException as error:
        log.error(f"{name} subscription delete failed: {error}")

def terminator(signum, frame):
    log.info("Terminating...")
    subscriptions_to_delete = [
        ("AMF registration", amf_sub),
        ("AMF location", amf_sub_location),
        ("SMF PDU session", smf_sub),
        ("SMF QoS monitoring", smf_sub_qos_mon),
        ("NWDAF network performance", net_per_sub),
        ("NWDAF anomaly", anomaly_sub),
        ("NWDAF track UE location", track_ue_sub),
    ]
    # Daemon threads, so a deletion still hanging at the deadline cannot block the exit.
    threads = [threading.Thread(target=delete_subscription, args=(name, url), daemon=True)
               for name, url in subscriptions_to_delete if url != ""]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + SHUTDOWN_DEADLINE
    for thread in threads:
        thread.join(max(0, deadline - time.monotonic()))
    if any(thread.is_alive() for thread in threads):
        log.warning(f"Some subscription deletions did not finish within {SHUTDOWN_DEADLINE}s")
    sys.exit(0)


# Registered before the first subscription is created, so a SIGTERM during startup still cleans up.
signal.signal(signal.SIGTERM, terminator)
signal.signal(signal.SIGINT, terminator)

# -------------------Initialize CN_subscriptions----------------------------------------------------------------

log.info("Subscribing to Registration Events from AMF")
amf_endpoint = subscriptions.get_amf_subscription_url(amf_addr , amf_port , amf_url)
amf_sub = subscriptions.create_amf_subscription(amf_endpoint , sbi_addr , sbi_port , "REGISTRATION_STATE_REPORT")
amf_sub_location = subscriptions.create_amf_subscription(amf_endpoint , sbi_addr , sbi_port , "LOCATION_REPORT")

log.info("Subscribing to User Sessions Events from SMF")

smf_endpoint = subscriptions.get_smf_subscription_url(smf_addr , smf_port , smf_url)
smf_sub = subscriptions.create_smf_subscription(smf_endpoint , sbi_addr , sbi_port , "PDU_SES_EST" )
smf_sub_qos_mon = subscriptions.create_smf_subscription(smf_endpoint , sbi_addr , sbi_port , "QOS_MON" )

if amf_sub == "" or smf_sub == "":
    log.error("Subscription to CN events failed... Exiting \n check AMF and SMF connectivity")
    with open(status_file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    data['handler_status'] = 'off'  
    data['handler_pid'] = 'None' 
    with open(status_file_path, 'w') as file:
        yaml.safe_dump(data, file)
        
    assert False, "Subscription to CN events failed"

#--------------------------Initialize_NWDAF_subscriptions-------------------------------------------------------
log.info("Subscribing to NWDAF network performance")
net_per_endpoint = subscriptions.get_network_performance_subscription_url(nwdaf_name, nwdaf_url)
net_per_sub = subscriptions.create_network_performance_subscription(net_per_endpoint, sbi_addr , sbi_port , nwdaf_url)

log.info("Subscribing to NWDAF anomaly")
anomaly_endpoint = subscriptions.get_anomaly_subscription_url(nwdaf_name, nwdaf_url)
anomaly_sub = subscriptions.create_anomaly_subscription(sbi_addr , sbi_port , anomaly_endpoint ,nwdaf_url )

log.info("Subscribing to NWDAF track UE location")
track_ue_endpoint = subscriptions. get_track_ue_location_url(nwdaf_name , nwdaf_url)
track_ue_sub = subscriptions.create_track_ue_location(sbi_addr, sbi_port, track_ue_endpoint, nwdaf_url )

def connected_ues():

    existing_users = {}

    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            ran_ue_ngap_id = report["ranUeNgapId"]
            rm_state = report["rmInfoList"][0]["rmState"]
            timestamp = report["timeStamp"]

            if supi in existing_users:
                if timestamp > existing_users[supi]['timestamp']:
                    existing_users[supi] = {'supi': supi, 'ran_ue_ngap_id': ran_ue_ngap_id, 'rm_state': rm_state, 'timestamp': timestamp}
            else:
                existing_users[supi] = {'supi': supi, 'ran_ue_ngap_id': ran_ue_ngap_id, 'rm_state': rm_state, 'timestamp': timestamp}

    keys_to_remove = []
    
    for supi, user_info in existing_users.items():
        if user_info['rm_state'] != "REGISTERED":
            keys_to_remove.append(supi)

    for key in keys_to_remove:
        existing_users.pop(key)
    
    return existing_users


# handle the callbacks for registered UEs
def handle_registered_ue_callbacks():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    events_json_path = os.path.join(current_dir, '..', 'modules', 'events.json')
    with open(events_json_path, 'r') as json_file:
        data = json.load(json_file)
    registered_users = connected_ues()

    if data["events"]["RegisteredUEs"]["callbacks"] and registered_users:
        last_registered_user = list(registered_users.values())[-1]
        for callback_name in data["events"]["RegisteredUEs"]["callbacks"]:
            callback_function = getattr(callbacks, callback_name, None)
            if callback_function:
                callback_function(last_registered_user)

def handle_ue_traffic_callbacks(volume):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    events_json_path = os.path.join(current_dir, '..', 'modules', 'events.json')
    with open(events_json_path, 'r') as json_file:
        data = json.load(json_file)
    
    for callback_name in data["events"]["UETraffic"]["callbacks"]:
        callback_function = getattr(callbacks, callback_name, None)
        if callback_function:
            callback_function(volume)
    
def handle_changed_status_callbacks():
    global changed_status_dict
    latest_status_dict = {}

    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            ran_ue_ngap_id_amf = report["ranUeNgapId"]
            rm_state_amf = report["rmInfoList"][0]["rmState"]
            timestamp = report["timeStamp"]

            if supi not in latest_status_dict or timestamp > latest_status_dict[supi]['timestamp_amf']:
                latest_status_dict[supi] = {
                    'supi': supi,
                    'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                    'rmState_amf': rm_state_amf,
                    'timestamp_amf': timestamp
                }

    for supi, status in latest_status_dict.items():
        if supi in changed_status_dict:
            if status['rmState_amf'] != changed_status_dict[supi]['rmState_amf']:
                temp_dict = {supi: status}

                current_dir = os.path.dirname(os.path.abspath(__file__))
                events_json_path = os.path.join(current_dir, '..', 'modules', 'events.json')

                with open(events_json_path, 'r') as json_file:
                    data = json.load(json_file)

                if data["events"]["UEStatus"]["callbacks"]:
                    for callback_name in data["events"]["UEStatus"]["callbacks"]:
                        callback_function = getattr(callbacks, callback_name, None)
                        if callback_function:
                            callback_function(temp_dict)

        changed_status_dict[supi] = status

# Route for AMF notifications
@app.route('/callbacks/amf-reports', methods=['POST'])
def receive_amf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)

        event_notifs = content.get('reportList', [])
        for notif in event_notifs:
            event = notif.get('type', '')
            if event == 'LOCATION_REPORT':
                amf_location_collection.insert_one(content)
            else:
                if event == 'REGISTRATION_STATE_REPORT':
                    amf_collection.insert_one(content)
                try:
                    importlib.reload(callbacks)
                    handle_registered_ue_callbacks()
                except Exception as e:
                    log.error(f"Error in handle_registered_ue_callbacks: {e}")
                
                try:
                    handle_changed_status_callbacks()
                except Exception as e:
                    log.error(f"Error in handle_changed_status_callbacks: {e}")

    return "OK"


# Route for SMF notifications
@app.route('/callbacks/dataplane-reports', methods=['POST'])
def receive_smf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)
        
        # Process the notifications based on the event type
        event_notifs = content.get('eventNotifs', [])
        for notif in event_notifs:
            event = notif.get('event', '')
            if event == 'QOS_MON':
                smf_traffic_collection.insert_one(content)
                usage_report = notif.get('customized_data', {}).get('Usage Report', {})
                volume_dict = {
                    'Downlink': usage_report.get('Volume', {}).get('Downlink', 0),
                    'Uplink': usage_report.get('Volume', {}).get('Uplink', 0)
                }
                
                importlib.reload(callbacks)

                try :
                    handle_ue_traffic_callbacks(volume_dict)
                except Exception as e:
                    log.error(f"Error in handle_ue_traffic_callbacks: {e}")
            else:
                smf_collection.insert_one(content)

    return "OK"


@app.route('/notification', methods=[ 'POST'])

def receive_location_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)
        return "OK"


@app.route('/anomaly_notification', methods=['POST'])
def receive_anomaly_notification():
    content = request.get_json(force=True)
    log.info('ANOMALY')
    log.info(content)
    return "OK"

@app.route('/network_performance_notification', methods=['POST'])
def receive_network_performance_notification():
    global net_perf_res
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info('NETWORK PERFORMANCE')
        log.info(content)
        return "OK"
    




if __name__ == "__main__":
    app.run(host=sbi_addr, port=sbi_port, debug=False)
