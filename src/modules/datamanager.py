import csv
import os
from data_models.DataStream import DataStream
from data_models.Metric import Metric
from pymongo import MongoClient 
import operator
import logging 
def createDataStream(data_selection=[], filters=None, callback=None):
    """
    Create a new data stream
    
    Parameters:
    data_selection (list): List of metrics to be selected
    filters (list): List of filters to be applied to the data stream: [(metric, operator, value), ...]
    callback (function): Callback function to be called when data is received

    Returns:
    DataStream: DataStream object
    """
    
    data_stream = DataStream(data_selection=data_selection, filters=filters, callback=callback)
    return data_stream

def saveDataStream(data_stream, filename):
    """
    Save a DataStream to a CSV file in the user's Documents directory

    Parameters:
    data_stream (DataStream): The DataStream object to save
    filename (str): The name of the file to save the data to
    """
    # Get the path to the user's Documents directory
    documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
    full_path = os.path.join(documents_dir, filename)
    
    # Ensure the directory exists
    if not os.path.exists(documents_dir):
        os.makedirs(documents_dir, exist_ok=True)

    # Define the callback function that will save data to CSV
    def csv_callback(entry):
        file_exists = os.path.isfile(full_path)
        
        # Open the file in append mode
        with open(full_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write the header if the file does not exist
            if not file_exists:
                header = [metric.name for metric in data_stream.data_selection]
                writer.writerow(header)
            
            # Write the data entry
            row = [getattr(entry, metric.name) for metric in data_stream.data_selection]
            writer.writerow(row)

    # Set the callback for the data stream
    data_stream.callback = csv_callback

# Example usage


def create_data_stream(data_selection=None , filters=None ):
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
    logging.getLogger('pymongo').setLevel(logging.WARNING)

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

    data_bank=[
        {
            'imsi': supi,
            **data
        }
        for supi, data in registration_state_report.items()
    ]
    if data_selection==None:
        return data_bank
    
    data_selection=[metric.value for metric in data_selection]
    i=0
    for ue_report in data_bank:
        updated_report = {}
        i+=1
        updated_report['raw_id'] = i

        for k, v in ue_report.items():
            if k in data_selection:
                updated_report[k] = v
        processed_data.append(updated_report)
    

    

    if filters==None:
        return processed_data
        
    operators = {
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le
}


    for report in processed_data:
        include = True
        for key, op, value in filters:
            if key in report:
                if not operators[op](report[key], value):
                    include = False
                    break
        if include:
            filtered_data.append(report)

    return filtered_data

def save_data_to_csv(data, output_file='data_streams.csv'):
    """
    Save the data to a CSV file, filling in None for any missing values.
    
    Parameters:
    data (list of dict): The data to be saved. Each dict represents a row in the CSV.
    output_file (str): Path to the file where data will be saved.
    
    Returns:
    None
    """
    if not data:
        print("No data to save.")
        return

    # Get the headers from the keys of the first item
    headers = data[0].keys()
    
    try:
        with open(output_file, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()

            # Ensure that each row has all keys, filling missing ones with None
            for row in data:
                filled_row = {key: row.get(key, None) for key in headers}
                writer.writerow(filled_row)

        print(f"Data successfully saved to {output_file}")
    except Exception as e:
        print(f"An error occurred while saving data: {e}")


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
filters = [
    ('registration_status', '==', 'REGISTERED')]
#a=create_data_stream(data_selection)
#print(a)
#save_data_to_csv(a , 'hhh.csv')
#print(data_selection[1].value)




