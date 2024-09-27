
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
from flask import Flask, request , jsonify
from pymongo import MongoClient , errors
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


nwdaf_name= data['nwdaf-sbi']['name']
nwdaf_url =  data['nwdaf-sbi']['url']



app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
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

    raise AssertionError("Failed to connect to MongoDB")

db = client['notification_db']
nwdaf_location_collection= db['nwdaf_location_traffic']

log.info("Successfully connected to MongoDB.")




# Initialize MongoDB collections


# Clean collections
def clean_collections():

    nwdaf_location_collection.delete_many({})
    log.info("Collections cleaned.")
    
clean_collections()


#--------------------------Initialize_NWDAF_subscriptions-------------------------------------------------------
log.info("Subscribing to NWDAF network performance")

net_per_endpoint = subscriptions.get_network_performance_subscription_url(nwdaf_name, nwdaf_url)
net_per_sub = subscriptions.create_network_performance_subscription(net_per_endpoint, sbi_addr , sbi_port , nwdaf_url)

log.info("Subscribing to NWDAF anomaly")
#anomaly_endpoint = subscriptions.get_anomaly_subscription_url(nwdaf_name, nwdaf_url)
#anomaly_sub = subscriptions.create_anomaly_subscription(sbi_addr , sbi_port , anomaly_endpoint ,nwdaf_url )

log.info("Subscribing to NWDAF track UE location")
#track_ue_endpoint = subscriptions. get_track_ue_location_url(nwdaf_name , nwdaf_url)
#track_ue_sub = subscriptions.create_track_ue_location(sbi_addr, sbi_port, track_ue_endpoint, nwdaf_url )


@app.route('/notification', methods=[ 'POST'])

def receive_location_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.debug(content)
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
    app.run(host=sbi_addr, port=1112,debug=True )

# Define termination handler
def terminator(signum, frame, ask=True):
    log.info("Terminating...")

    if net_per_sub != "":
        url = net_per_sub
        response = requests.delete(url)
        log.info(f"Network Performance Subscription delete status code: {response.status_code}")

   # if anomaly_sub != "":
    #    url = anomaly_sub
     #   response = requests.delete(url)
      #  log.info(f"Anomaly Subscription delete status code: {response.status_code}")

 #   if track_ue_sub != "":
  #      url = track_ue_sub
   #     response = requests.delete(url)
    #    log.info(f"Track UE Location Subscription delete status code: {response.status_code}")


signal.signal(signal.SIGTERM, terminator)
signal.signal(signal.SIGINT, terminator)
signal.pause()
