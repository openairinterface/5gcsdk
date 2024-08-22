import sys
import os 
from datetime import datetime
current_dir = os.path.dirname(os.path.abspath(__file__))
src_main_dir = os.path.join(current_dir, '../src/main')
sys.path.append(src_main_dir)

import oai5gc

oai5gc.stop_handler()


#oai5gc.RFsimUEManager.add_ues(1)

#print(oai5gc.UEManager.get_registered_ues())

#oai5gc.RFsimUEManager.remove_ues(1)
data_selection = [
        oai5gc.Metric.timestamp,
        oai5gc.Metric.data_ul,
        oai5gc.Metric.data_dl,
        oai5gc.Metric.number_pkts_ul,
        oai5gc.Metric.number_pkts_dl,
        oai5gc.Metric.connectivity_status,
        oai5gc.Metric.ip_address,
        oai5gc.Metric.imsi,
        oai5gc.Metric.dnn,
        oai5gc.Metric.sst,
        oai5gc.Metric.sd,
        oai5gc.Metric.plmn,
        oai5gc.Metric.amf_ngap_id,
        oai5gc.Metric.gnb_ngap_id,
        oai5gc.Metric.cell_id,
        oai5gc.Metric.registration_status
]
#a=oai5gc.create_data_stream()
#oai5gc.save_data_to_csv(a , 'dataa.csv')

#oai5gc.UEManager.get_ue_status('12.1.1.130')
#12.1.1.2
def sample_callback(data):
   print("UE DATA :", data)
#def callback(ue) :
    #print("ue connected" , ue)

#def sample_callback2(data):
  #   imsi = list(data.keys())[0]
 #    print("A UE status is updated with imsi:", imsi)
#a=oai5gc.EventType.DATA_STREAM
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
#smf_notification_traffic_collection = db['amf_location_notification']
#total_uplink=0
#total_downlink = 0

#query = {
#        'timeStamp': {'$gte': '3929693438', '$lte': '3929693899'}
 #   }
    #if ue_supi:

    # Retrieve records from the database
#records = smf_notification_traffic_collection.find(query)
 #Retrieve and print all documents in the smf_notification_traffic collection

new_report = {
    '_id': '66a78c94161a684b5029a0f2',  # Use a unique ObjectId or let MongoDB auto-generate
    'notifyCorrelationId': '05d77254-4da7-11ef-af2d-b747da03aefb',
    'reportList': [
        {
            'location': {
                'nrLocation': {
                    'globalGnbId': {
                        'gNbId': {
                            'bitLength': 32,
                            'gNBValue': '12345'
                        },
                        'plmnId': {
                            'mcc': '208',
                            'mnc': '98'
                        }
                    },
                    'ncgi': {
                        'nrCellId': '24',
                        'plmnId': {
                            'mcc': '',
                            'mnc': ''
                        }
                    },
                    'tai': {
                        'plmnId': {
                            'mcc': '208',
                            'mnc': '98'
                        },
                        'tac': '2'
                    }
                }
            },
            'state': {'active': False},
            'supi': 'imsi-208990000000034',
            'timeStamp': 1722256540,
            'type': 'LOCATION_REPORT'
        }
    ]
}

# Insert the new document into the collection
#result = smf_notification_traffic_collection.insert_one(new_report)
#documents = smf_notification_traffic_collection.find()
#for doc in documents:
 #   print(doc)
    #report = doc['reportList'][0]
    #print(report)    
        # Access the location details
    #location = report.get('location', {})
    #ncgi= location['nrLocation']['tai']['tac']

    #print(ncgi)
    #print(doc)
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




#start_timestamp = int(datetime.strptime('39292452444', "%Y-%m-%d %H:%M:%S").timestamp())
#print(start_timestamp)