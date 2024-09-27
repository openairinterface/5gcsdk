import csv
from pymongo import MongoClient 
import operator
import logging
from data_models.Metric import Metric 
from enum import Enum


def create_data_stream(data_selection=None, filters=None):
    """
    This function creates a new data stream by retrieving and processing UE (User Equipment) data from various MongoDB collections.

    :param data_selection: List of metrics to be selected. If None, all data is returned. 
    :type data_selection: list, optional
    :param filters: List of filters to be applied to the data stream in the format [(metric, operator, value), ...]. 
                    If None, no filtering is applied.
    :type filters: list, optional
    :return: A list of dictionaries containing the processed data stream, with each dictionary representing a UE with selected metrics.
    :rtype: list

    :raises AssertionError: If any of the required MongoDB collections are not found.
    :raises ValueError: If an invalid operator is used in the filters.
    :raises Exception: For any other errors that occur during data retrieval and processing.

    Usage Example:
    --------------
    >>> data_selection = [Metrics.IMSI, Metrics.IP_ADDRESS]
    >>> filters = [('registration_status', '==', 'REGISTERED'), ('data_dl', '>', 1000)]
    >>> data_stream = create_data_stream(data_selection, filters)
    >>> print(data_stream)
    """

    # Initialize MongoDB client
    client = MongoClient('mongodb://localhost:27017/')
    logging.getLogger('pymongo').setLevel(logging.WARNING)

    # Access the database
    db = client['notification_db']

    # Assert that all necessary collections exist
    required_collections = [
        'amf_notifications', 
        'amf_location_notification', 
        'smf_notifications', 
        'smf_notification_traffic'
    ]
    for collection in required_collections:
        assert collection in db.list_collection_names(), f"{collection} collection not found in the database"

    # Access collections
    amf_collection = db['amf_notifications']
    amf_location_collection = db['amf_location_notification']
    smf_collection = db['smf_notifications']
    smf_traffic_collection = db['smf_notification_traffic']

    # Initialize variables
    processed_data = []
    existing_ues = []
    filtered_data = []
    registration_state_report = {}

    # Populate list of existing UEs
    for document in amf_collection.find():
        for report in document["reportList"]:
            latest_timestamp = 0
            supi = report["supi"]
            if supi not in existing_ues:
                existing_ues.append(supi)

    # Process AMF collection data
    for document in amf_collection.find():
        for report in document["reportList"]:
            for supi in existing_ues:
                timestamp = report["timeStamp"]

                if report["supi"] == supi and timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    registration_state_report[supi] = {
                        'amf_ngap_id': report['amfUeNgapId'],
                        'gnb_ngap_id': report['ranUeNgapId'],
                        'registration_status': report['rmInfoList'][0]['rmState'],
                    }

    # Process SMF collection data
    latest_timestamp = 0
    for document in smf_collection.find():
        for report in document["eventNotifs"]:
            for supi in existing_ues:
                timestamp = report["timeStamp"]
                imsi = f'imsi-{report["supi"]}'
                if imsi == supi and int(timestamp) > int(latest_timestamp):
                    latest_timestamp = timestamp
                    registration_state_report[supi].update({
                        'ip_address': report['adIpv4Addr'],
                        'dnn': report['dnn'],
                        'sd': report['snssai']['sd'],
                        'sst': report['snssai']['sst'],
                    })

    # Process AMF location collection data
    latest_timestamp = 0
    for document in amf_location_collection.find():
        for report in document["reportList"]:
            for supi in existing_ues:
                timestamp = report["timeStamp"]

                if report["supi"] == supi and int(timestamp) > int(latest_timestamp):
                    latest_timestamp = timestamp
                    registration_state_report[supi].update({
                        'cell_id': report['location']['nrLocation']['tai']['tac'],
                        'plmn': report['location']['nrLocation']['globalGnbId']['plmnId'],
                    })

    # Process SMF traffic collection data
    latest_timestamp = 0
    for document in smf_traffic_collection.find():
        for report in document["eventNotifs"]:
            for supi in existing_ues:
                timestamp = report["timeStamp"]
                imsi = f'imsi-{report["supi"]}'
                if imsi == supi and int(timestamp) > int(latest_timestamp):
                    latest_timestamp = timestamp
                    registration_state_report[supi].update({
                        'number_pkts_dl': report['customized_data']['Usage Report']['NoP']['Downlink'],
                        'number_pkts_ul': report['customized_data']['Usage Report']['NoP']['Uplink'],
                        'data_dl': report['customized_data']['Usage Report']['Volume']['Downlink'],
                        'data_ul': report['customized_data']['Usage Report']['Volume']['Uplink'],
                    })

    # Prepare the data bank
    data_bank = [
        {
            'imsi': supi,
            **data
        }
        for supi, data in registration_state_report.items()
    ]

    # If no data selection is specified, return the full data bank
    if data_selection is None:
        return data_bank

    # Filter the data according to the selected metrics
    data_selection = [metric.value for metric in data_selection]
    i = 0
    for ue_report in data_bank:
        updated_report = {}
        i += 1
        updated_report['raw_id'] = i

        for k, v in ue_report.items():
            if k in data_selection:
                updated_report[k] = v
        processed_data.append(updated_report)

    # If no filters are specified, return the processed data
    if filters is None:
        return processed_data

    # Define valid operators
    operators = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le
    }

    # Apply the filters
    for report in processed_data:
        include = True
        for key, op, value in filters:
            if key in report:
                if op not in operators:
                    raise ValueError(f"Invalid operator: {op}")
                if not operators[op](report[key], value):
                    include = False
                    break
        if include:
            filtered_data.append(report)

    return filtered_data

def save_data_to_csv(data, output_file='data_streams.csv'):
    """
    Saves the provided data to a CSV file, filling in None for any missing values.

    :param data: The data to be saved. Each dictionary in the list represents a row in the CSV file.
    :type data: list of dict
    :param output_file: The file path where the data will be saved. Defaults to 'data_streams.csv'.
    :type output_file: str, optional
    :return: None
    :rtype: None

    :raises Exception: If an error occurs while saving data to the CSV file.

    Usage Example:
    --------------
    >>> data_selection = [Metrics.IMSI, Metrics.IP_ADDRESS]
    >>> filters = [('registration_status', '==', 'REGISTERED'), ('data_dl', '>', 1000)]
    >>> data_stream = create_data_stream(data_selection, filters)
    >>> save_data_to_csv(data, 'output.csv')
    >>> print("Data saved successfully.")
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







