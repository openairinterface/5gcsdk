# SPDX-License-Identifier: MIT

import sys
import os 

current_dir = os.path.dirname(os.path.abspath(__file__))
src_main_dir = os.path.join(current_dir, '../src/main')
sys.path.append(src_main_dir)

import oai5gc

oai5gc.stop_handler()


#oai5gc.RFsimUEManager.add_ues(2)

#print(oai5gc.UEManager.get_registered_ues())

#oai5gc.RFsimUEManager.remove_ues(3)

oai5gc.UEManager.get_ue_status('12.1.1.130')
#12.1.1.2
def sample_callback(data):
   print("New UE is registred with credentials:", data)
#def callback(ue) :
    #print("ue connected" , ue)

#def sample_callback2(data):
  #   imsi = list(data.keys())[0]
 #    print("A UE status is updated with imsi:", imsi)
#a=oai5gc.EventType.REGISTERED_UES
#oai5gc.register_callback_ue(sample_callback, a)
#oai5gc.unregister_callback_ue()
#oai5gc.register_callback_ue(sample_callback2, "UEStatus")

#oai5gc.add_ues(2)

#oai5gc.RFsimUEManager.remove_ues(1)


#from pymongo import MongoClient
#import pprint

# MongoDB connection setup
#client = MongoClient('mongodb://localhost:27017/')
#db = client['notification_db']
#smf_notification_traffic_collection = db['amf_notifications']
#total_uplink=0
#total_downlink = 0

#query = {
#        'timeStamp': {'$gte': '3929693438', '$lte': '3929693899'}
 #   }
    #if ue_supi:

    # Retrieve records from the database
#records = smf_notification_traffic_collection.find(query)
 #Retrieve and print all documents in the smf_notification_traffic collection
#documents = smf_notification_traffic_collection.find()
#for doc in documents:
   # print(doc)
    #usage_report = doc.get('customized_data', {}).get('Usage Report', {})
    #total_uplink += usage_report.get('Volume', {}).get('Uplink')
    #total_downlink += usage_report.get('Volume', {}).get('Downlink')
    #print(total_downlink)

#from datetime import datetime


# Example timestamps
#start_timestamp = 3929693438
#end_timestamp = 3929693899
# convert the timestamp to a datetime object in the local timezone
#dt_object = datetime.fromtimestamp(end_timestamp)

# print the datetime object and its type
#print("dt_object =", dt_object)
#print("type(dt_object) =", type(dt_object))
