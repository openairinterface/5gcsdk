

import signal
import requests
from flask import Flask, request
from pymongo import MongoClient
from subscriptions_manager.subscriptions import createSmfSubscription, createAmfSubscription , getAmfSubscriptionUrl , getSmfSubscriptionUrl
import logging

app = Flask(__name__)

# Initialize MongoDB connection
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

# Route for AMF notifications
@app.route('/callbacks/amf-reports', methods=['POST'])
def receive_amf_notification():
    if request.method == 'POST':
        content = request.get_json(force=True)
        log.info(content)
        amf_collection.insert_one(content) 
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


