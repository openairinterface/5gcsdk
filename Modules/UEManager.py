from pymongo import MongoClient

def get_registered_UEs():
    """
    Retrieves registered users from the MongoDB collections.

    This function connects to the MongoDB database and retrieves users from the
    'amf_notifications' collection. It extracts information such as SUPI, RAN UE NGAP ID,
    and RM State for each user.

    :return: A list of dictionaries containing user information.
    :rtype: list
    """

    
    client         = MongoClient('mongodb://localhost:27017/')  
    db             = client['notification_db']
    amf_collection = db['amf_notifications']
    smf_collection = db['smf_notifications']
   
    existing_users = {}

    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            ran_ue_ngap_id_amf = report["ranUeNgapId"]
            rm_state_amf = report["rmInfoList"][0]["rmState"]
            timestamp = report["timeStamp"]

            # Check if the user is already in the dictionary
            if supi in existing_users:
                # If the current notification has a newer timestamp, update the information
                if timestamp > existing_users[supi]['timestamp_amf']:
                    existing_users[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf, 'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}
            else:
                # If the user is not in the dictionary, add them
                existing_users[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf, 'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

    keys_to_remove = []
    
    # Iterate over existing users and mark users to remove
    for supi, user_info in existing_users.items():
        if user_info['rmState_amf'] != "REGISTERED":
            keys_to_remove.append(supi)

    # Remove the marked users
    for key in keys_to_remove:
        existing_users.pop(key)
    
    
    return existing_users
def get_changed_status_UEs():
    """
    Retrieves registered users from the MongoDB collections.

    This function connects to the MongoDB database and retrieves users from the
    'amf_notifications' collection. It extracts information such as SUPI, RAN UE NGAP ID,
    and RM State for each user.

    :return: A list of dictionaries containing user information for each timestamp.
    :rtype: list
    """

    # Connect to the MongoDB database
    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']
    amf_collection = db['amf_notifications']
    
    existing_users = {}

    # Iterate over documents in the 'amf_notifications' collection
    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            ran_ue_ngap_id_amf = report["ranUeNgapId"]
            rm_state_amf = report["rmInfoList"][0]["rmState"]
            timestamp = report["timeStamp"]

            # Check if the user is already in the dictionary
            if supi in existing_users:
                # If the current notification has a newer timestamp, update the information
                if timestamp > existing_users[supi]['timestamp_amf']:
                    existing_users[supi]['timestamp_amf'] = timestamp
                    existing_users[supi]['rmState_amf'] = rm_state_amf
            else:
                # If the user is not in the dictionary, add them
                existing_users[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf, 'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

    # Filter users with at least 2 different timestamps
    changed_users = []

    for supi, user_info in existing_users.items():
        timestamps = {user_info['timestamp_amf']}
        for document in amf_collection.find({'reportList.supi': supi}):
            for report in document["reportList"]:
                timestamps.add(report["timeStamp"])

        if len(timestamps) >= 2:
            user_info['timestamps'] = list(timestamps)
            changed_users.append(user_info)

    return changed_users




def get_ue_status_by_imsi(imsi):
    """
    Retrieves the status of a registered UE by its IMSI.

    This function takes the IMSI of a UE as input and returns its status, if
    the UE is registered. If the IMSI is not found in the database, it returns
    'UE not found'.

    :param imsi: The IMSI (International Mobile Subscriber Identity) of the UE.
    :type imsi: str
    :return: The status of the UE or 'UE not found' if IMSI is not found.
    :rtype: str
    """

    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']
    amf_collection = db['amf_notifications']
   
    latest_timestamp = 0
    latest_rm_state = None

    # Iterate over documents in the collection
    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            if supi == imsi:
                # Check if the timestamp is the latest
                if report["timeStamp"] > latest_timestamp:
                    latest_timestamp = report["timeStamp"]
                    latest_rm_state = report["rmInfoList"][0]["rmState"]

    # If a latest status is found, return it; otherwise, return 'UE not found'
    if latest_rm_state:
        return print(f"status of UE with IMSI {imsi} : {latest_rm_state}")
    else:
        return print('UE not found')
