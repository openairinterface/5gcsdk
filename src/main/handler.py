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
import requests
import subprocess
import datamanager as datastream
from NwdafManager import get_anomaly_ratio
from flask import Flask, request , jsonify
from pymongo import MongoClient , errors
import httpx
import subscriptions as subscriptions

import logging
import json
import importlib
import yaml
from yaml.loader import SafeLoader
import operator
from data_models.ue import UE


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

http_version= data['http_version']
if http_version == 2 : 
    http_2=True 
    http_1=False
if http_version == 1 : 
    http_2=False  
    http_1=True     

changed_status_dict = {}
changed_cellid_dict = {}
data_selection = [
        Metric.timestamp,
        Metric.data_ul,
        Metric.data_dl,
        Metric.number_pkts_ul,
        Metric.number_pkts_dl,
        Metric.connectivity_status,
        Metric.ip_address,
        Metric.imsi,
        Metric.dnn,
        Metric.sst,
        Metric.sd,
        Metric.plmn,
        Metric.amf_ngap_id,
        Metric.gnb_ngap_id,
        Metric.cell_id,
        Metric.registration_status
]
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
nwdaf_anomaly_collection= db['nwdaf_anomaly_notification']


log.info("Successfully connected to MongoDB.")




# Initialize MongoDB collections


# Clean collections
def clean_collections():
    amf_collection.delete_many({})
    smf_collection.delete_many({})
    smf_traffic_collection.delete_many({})
    amf_location_collection.delete_many({})
    nwdaf_anomaly_collection.delete_many({})

    log.info("Collections cleaned.")
    
clean_collections()

# -------------------Initialize CN_subscriptions----------------------------------------------------------------

log.info("Subscribing to Registration Events from AMF")
amf_endpoint = subscriptions.get_amf_subscription_url(amf_addr , amf_port , amf_url)
amf_sub = subscriptions.create_amf_subscription(amf_endpoint , sbi_addr , sbi_port , "REGISTRATION_STATE_REPORT" , http_version)
#amf_sub_location = subscriptions.create_amf_subscription(amf_endpoint , sbi_addr , sbi_port , "LOCATION_REPORT", http_version)
#amf_connectivity = subscriptions.create_amf_subscription(amf_endpoint , sbi_addr , sbi_port , "CONNECTIVITY_STATE_REPORT" , http_version)

log.info("Subscribing to User Sessions Events from SMF")

smf_endpoint = subscriptions.get_smf_subscription_url(smf_addr , smf_port , smf_url)
smf_sub = subscriptions.create_smf_subscription(smf_endpoint , sbi_addr , sbi_port , "PDU_SES_EST" , http_version )
#smf_sub_qos_mon = subscriptions.create_smf_subscription(smf_endpoint , sbi_addr , sbi_port , "QOS_MON" )

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
#log.info("Subscribing to NWDAF network performance")
#net_per_endpoint = subscriptions.get_network_performance_subscription_url(nwdaf_name, nwdaf_url)
#net_per_sub = subscriptions.create_network_performance_subscription(net_per_endpoint, sbi_addr , sbi_port , nwdaf_url)

log.info("Subscribing to NWDAF anomaly")
anomaly_endpoint = subscriptions.get_anomaly_subscription_url(nwdaf_name, nwdaf_url)
anomaly_sub = subscriptions.create_anomaly_subscription(sbi_addr , sbi_port , anomaly_endpoint ,nwdaf_url )

#log.info("Subscribing to NWDAF track UE location")
#track_ue_endpoint = subscriptions. get_track_ue_location_url(nwdaf_name , nwdaf_url)
#track_ue_sub = subscriptions.create_track_ue_location(sbi_addr, sbi_port, track_ue_endpoint, nwdaf_url )

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

def create_row_stream():
    """
    Create a new data stream
    
    Parameters:
    data_selection (list): List of metrics to be selected
    filters (list): List of filters to be applied to the data stream: [(metric, operator, value), ...]
    callback (function): Callback function to be called when data is received

    Returns:
    DataStream: DataStream object
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']
    amf_collection = db['amf_notifications']
    amf_location_collection = db['amf_location_notification']
    smf_collection = db['smf_notifications']
    smf_traffic_collection = db['smf_notification_traffic']
    processed_data = []
    existing_ues = []
    filtered_data=[]
    registration_state_report={}

    for document in amf_collection.find():
        for report in document["reportList"]:
            latest_timestamp=0
            supi = report["supi"]
            if supi not in existing_ues:
                existing_ues.append(supi)

    # Retrieve data from AMF collection
    for document in amf_collection.find():
        for report in document["reportList"]:
            for supi in existing_ues :
                timestamp = report["timeStamp"]

                if report["supi"]==supi and timestamp>latest_timestamp :
                    latest_timestamp= timestamp
                    registration_state_report[supi] = {
                        'amf_ngap_id': report['amfUeNgapId'],
                        'gnb_ngap_id': report['ranUeNgapId'],
                        'registration_status': report['rmInfoList'][0]['rmState'],
                    }

    latest_timestamp=0
    for document in smf_collection.find():
        for report in document["eventNotifs"]:
            for supi in existing_ues :
                timestamp = report["timeStamp"]
                imsi=str('imsi-')+str(report["supi"])
                if str(imsi)==str(supi) and int(timestamp)>int(latest_timestamp) :
                    latest_timestamp= timestamp
                    registration_state_report[supi].update( {
                        'ip_address': report['adIpv4Addr'],
                        'dnn': report['dnn'],
                        'sd': report['snssai']['sd'],
                        'sst': report['snssai']['sst'],

                    })

    latest_timestamp=0
    for document in amf_location_collection.find():
        for report in document["reportList"]:
            for supi in existing_ues :
                timestamp = report["timeStamp"]

                if report["supi"]==supi and int(timestamp)>int(latest_timestamp) :
                    latest_timestamp= timestamp
                    registration_state_report[supi].update( {
                        'cell_id': report['location']['nrLocation']['tai']['tac'],
                        'plmn': report['location']['nrLocation']['globalGnbId']['plmnId'],

                    })
    
    latest_timestamp=0
    for document in smf_traffic_collection.find():
        for report in document["eventNotifs"]:
            for supi in existing_ues :
                timestamp = report["timeStamp"]
                imsi=str('imsi-')+str(report["supi"])
                if str(imsi)==str(supi) and int(timestamp)>int(latest_timestamp) :
                    latest_timestamp= timestamp
                    registration_state_report[supi].update( {
                        'number_pkts_dl': report['customized_data']['Usage Report']['NoP']['Downlink'],
                        'number_pkts_ul': report['customized_data']['Usage Report']['NoP']['Uplink'],
                        'data_dl'       : report['customized_data']['Usage Report']['Volume']['Downlink'],
                        'data_ul'       : report['customized_data']['Usage Report']['Volume']['Uplink'],
                    })

    # Initialize a counter

    # Create the data_bank with an additional 'row_number' field
    data_bank = [
        {
            'row_number': counter,
            'imsi': supi,
            **data
        }
        for counter, (supi, data) in enumerate(registration_state_report.items(), start=1)
    ]
   
    return data_bank[-1]
    


# handle the callbacks for registered UEs
def handle_registered_ue_callbacks():
    home_dir = os.path.expanduser("~")
    events_json_path = os.path.join(home_dir, '5gcsdk', 'src', 'modules', 'events.json')

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
    home_dir = os.path.expanduser("~")
    events_json_path = os.path.join(home_dir, '5gcsdk', 'src', 'modules', 'events.json')
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

                home_dir = os.path.expanduser("~")
                events_json_path = os.path.join(home_dir, '5gcsdk', 'src', 'modules', 'events.json')

                with open(events_json_path, 'r') as json_file:
                    data = json.load(json_file)

                if data["events"]["UEStatus"]["callbacks"]:
                    for callback_name in data["events"]["UEStatus"]["callbacks"]:
                        callback_function = getattr(callbacks, callback_name, None)
                        if callback_function:
                            callback_function(temp_dict)

        changed_status_dict[supi] = status

def handle_changed_cellid_callbacks():
    global changed_cellid_dict
    latest_cellid_dict = {}

    for document in amf_location_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            location = report.get('location', {})
            cell_id= location['nrLocation']['tai']['tac']
            timestamp = report["timeStamp"]

            if supi not in latest_cellid_dict or timestamp > latest_cellid_dict[supi]['timestamp']:
                latest_cellid_dict[supi] = {
                    'supi': supi,
                    'cellId': cell_id,
                    'timestamp': timestamp
                }

    for supi, status in latest_cellid_dict.items():
        if supi in changed_cellid_dict:
            if status['cellId'] != changed_cellid_dict[supi]['cellId']:
                temp_dict = {supi: status}

                home_dir = os.path.expanduser("~")
                events_json_path = os.path.join(home_dir, '5gcsdk', 'src', 'modules', 'events.json')

                with open(events_json_path, 'r') as json_file:
                    data = json.load(json_file)

                if data["events"]["CellIDChange"]["callbacks"]:
                    for callback_name in data["events"]["CellIDChange"]["callbacks"]:
                        callback_function = getattr(callbacks, callback_name, None)
                        if callback_function:
                            callback_function(temp_dict)

        changed_cellid_dict[supi] = status

def handle_data_stream_callbacks():
    home_dir = os.path.expanduser("~")
    events_json_path = os.path.join(home_dir, '5gcsdk', 'src', 'modules', 'events.json')
    with open(events_json_path, 'r') as json_file:
        data = json.load(json_file)
    
    for callback_name in data["events"]["DataStream"]["callbacks"]:
        row_stream= create_row_stream()
        ue_instance = UE(
                            supi=row_stream.get('imsi', ''),
                            ad_ipv4_addr=row_stream.get('ip_address', ''),
                            ran_ue_ngap_id=row_stream.get('gnb_ngap_id', ''),
                            rm_state=row_stream.get('registration_status', ''),
                                timestamp=row_stream.get('timestamp', ''),
                            amf_ngap_id=row_stream.get('amf_ngap_id', ''),
                            plmn=row_stream.get('plmn', ''),
                            cell_id=row_stream.get('cell_id', ''),
                            sd=row_stream.get('sd', ''),
                            sst=row_stream.get('sst', ''),
                            dnn=row_stream.get('dnn', ''),
                            number_pkts_dl=row_stream.get('number_pkts_dl', ''),
                            number_pkts_ul=row_stream.get('number_pkts_ul', ''),
                            data_ul=row_stream.get('data_ul', ''),
                            data_dl=row_stream.get('data_dl', '')
                        )        
        callback_function = getattr(callbacks, callback_name, None)
        if callback_function:
            callback_function(ue_instance)

def handle_anomaly_callbacks():
    home_dir = os.path.expanduser("~")
    events_json_path = os.path.join(home_dir, '5gcsdk', 'src', 'modules', 'events.json')
    with open(events_json_path, 'r') as json_file:
        data = json.load(json_file)
    
    for callback_name in data["events"]["Anomaly"]["callbacks"]:
        callback_function = getattr(callbacks, callback_name, None)
        if callback_function:
            anomaly_score=get_anomaly_ratio()
            callback_function(anomaly_score)

# Route for AMF notifications
@app.route('/callbacks/amf-reports', methods=['POST'])
def receive_amf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)
        #print('--------------------------------------------------------------------------------------',request.environ.get('SERVER_PROTOCOL'))

        event_notifs = content.get('reportList', [])
        for notif in event_notifs:
            event = notif.get('type', '')

            if event == 'LOCATION_REPORT':
                amf_location_collection.insert_one(content)
                try:
                    importlib.reload(callbacks)
                    handle_changed_cellid_callbacks()

                except Exception as e:
                    log.error(f"Error in handle_changed_cellid_callbacks: {e}")
                
            else:
                if event == 'REGISTRATION_STATE_REPORT':
                    amf_collection.insert_one(content)
                    for notif in event_notifs:
                        rminfolist=notif.get('rmInfoList',[])[0]
                        status=rminfolist.get('rmState', '')

                    if status== 'DEREGISTERED' :
                        try:
                            importlib.reload(callbacks)
                            handle_data_stream_callbacks()

                        except Exception as e:
                            log.error(f"Error in handle_data_stream_callbacks: {e}")

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
        #print('--------------------------------------------------------------------------------------',request.environ.get('SERVER_PROTOCOL'))
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


        try:
            importlib.reload(callbacks)
            handle_data_stream_callbacks()

        except Exception as e:
            log.error(f"Error in handle_data_stream_callbacks: {e}")


    return "OK"


@app.route('/notification', methods=[ 'POST'])

def receive_location_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info('LOCATION')

        log.debug(content)
        return "OK"


@app.route('/anomaly_notification', methods=['POST'])
def receive_anomaly_notification():
    content = request.get_json(force=True)
    log.info('ANOMALY')
    log.info(content)
    nwdaf_anomaly_collection.insert_one(content)
    try:
        importlib.reload(callbacks)
        handle_anomaly_callbacks()

    except Exception as e:
        log.error(f"Error in handle_anomaly_callbacks: {e}")

    return "OK"

@app.route('/network_performance_notification', methods=['POST'])
def receive_network_performance_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info('NETWORK PERFORMANCE')
        log.info(content)
        return "OK"
    



if __name__ == "__main__":
    app.run(host=sbi_addr, port=1112,debug=False )

# Define termination handler
def terminator(signum, frame, ask=True):
    log.info("Terminating...")

    if amf_sub != "":
       with httpx.Client(http2=http_2, http1=http_1) as client:
            url = amf_sub
            r = client.delete(url)
            print(r.status_code)
            log.info(f"AMF Subscription delete status code: {r.status_code}")

    if smf_sub != "":
       with httpx.Client(http2=http_2, http1=http_1) as client:  
            url=smf_sub
            print('--------------------------------------------------------------', url)
            r = client.delete(url)
            print(r.status_code)
            log.info(f"SMF Subscription delete status code: {r.status_code}")
    
    #if net_per_sub != "":
        #url = net_per_sub
        #response = requests.delete(url)
        #log.info(f"Network Performance Subscription delete status code: {response.status_code}")

    if anomaly_sub != "":
        url = anomaly_sub
        response = requests.delete(url)
        print(url)
        log.info(f"Anomaly Subscription delete status code: {response.status_code}")

    #if track_ue_sub != "":
        #url = track_ue_sub
        #response = requests.delete(url)
        #log.info(f"Track UE Location Subscription delete status code: {response.status_code}")

 

signal.signal(signal.SIGTERM, terminator)
signal.signal(signal.SIGINT, terminator)
signal.pause()
