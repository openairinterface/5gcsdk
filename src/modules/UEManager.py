import logging
from pymongo import MongoClient
import re
def _is_valid_ipv4(ip):

    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if pattern.match(ip):
        parts = ip.split('.')
        for part in parts:
            if int(part) < 0 or int(part) > 255:
                return False
        return True
    return False

def _is_valid_imsi(imsi):

    pattern = re.compile(r'^imsi-\d{15}$')
    return bool(pattern.match(imsi))


def get_registered_ues():
    """
    Retrieves registered users from the MongoDB collections.

    This function connects to the MongoDB database and retrieves users from the
    'amf_notifications' collection. It extracts information such as SUPI, RAN UE NGAP ID,
    and RM State for each user.

    :return: A list of dictionaries containing user information.
    :rtype: list
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    client = MongoClient('mongodb://localhost:27017/')
    db             = client['notification_db']
    amf_collection = db['amf_notifications']
    smf_collection = db['smf_notifications']
    existing_users = {}

    for document in amf_collection.find():
        for report in document["reportList"]:
            supi = report["supi"]
            ran_ue_ngap_id = report["ranUeNgapId"]
            rm_state = report["rmInfoList"][0]["rmState"]
            timestamp = report["timeStamp"]
            for data_plane in smf_collection.find():
                smf_supi = 'imsi-'+data_plane['eventNotifs'][0].get('supi')
                if smf_supi == supi:
                    ip_addr = data_plane['eventNotifs'][0].get('adIpv4Addr')
                    break
            # Check if the user is already in the dictionary
            if supi in existing_users:
                # If the current notification has a newer timestamp, update the information
                if timestamp > existing_users[supi]['timestamp']:
                    existing_users[supi] = {'supi': supi, 'adIpv4Addr':ip_addr , 'ran_ue_ngap_id': ran_ue_ngap_id, 'rm_state': rm_state, 'timestamp': timestamp}
            else:
                # If the user is not in the dictionary, add them
                existing_users[supi] = {'supi': supi, 'adIpv4Addr':ip_addr , 'ran_ue_ngap_id': ran_ue_ngap_id, 'rm_state': rm_state, 'timestamp': timestamp}

    keys_to_remove = []
    
    # Iterate over existing users and mark users to remove
    for supi, user_info in existing_users.items():
        if user_info['rm_state'] != "REGISTERED":
            keys_to_remove.append(supi)

    # Remove the marked users
    for key in keys_to_remove:
        existing_users.pop(key)
    
    logger.info("Registered users retrieved successfully.")
    return existing_users

def get_ue_status(ue_credentials):
    """
        Retrieves the status of a registered UE by its credentials (IMSI or IP Address).

        This function takes the IMSI (International Mobile Subscriber Identity) or IP Address
        of a UE as input and returns its status if the UE is registered. If the IMSI or IP Address
        is not found in the database, it returns 'UE not found'. If the input is invalid, it returns
        'Invalid IMSI or IP address'.

        :param ue_credentials: The IMSI or IP Address of the UE.
        :type ue_credentials: str
        :return: The status of the UE, 'UE not found' if the IMSI or IP Address is not found, or
                'Invalid IMSI or IP address' if the input is invalid.
        :rtype: str
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']
    amf_collection = db['amf_notifications']
    smf_collection = db['smf_notifications']
    
    if _is_valid_ipv4(ue_credentials):
            
            latest_timestamp = 0
            latest_rm_state = None
            for data_plane in smf_collection.find():
                ue_ip = data_plane['eventNotifs'][0].get('adIpv4Addr')
                if ue_credentials == ue_ip:
                    imsi = 'imsi-'+data_plane['eventNotifs'][0].get('supi')
                    break
                
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
                logger.info(f"Status of UE with IP {ue_credentials}: {latest_rm_state}")
                return latest_rm_state
            else:
                logger.info('UE not found')
                return 'UE not found'
            
    if _is_valid_imsi(ue_credentials):
        latest_timestamp = 0
        latest_rm_state = None

        # Iterate over documents in the collection
        for document in amf_collection.find():
            for report in document["reportList"]:
                supi = report["supi"]
                if supi == ue_credentials:
                    # Check if the timestamp is the latest
                    if report["timeStamp"] > latest_timestamp:
                        latest_timestamp = report["timeStamp"]
                        latest_rm_state = report["rmInfoList"][0]["rmState"]

        # If a latest status is found, return it; otherwise, return 'UE not found'
        if latest_rm_state:
            logger.info(f"Status of UE with IMSI {ue_credentials}: {latest_rm_state}")
            return latest_rm_state
        else:
            logger.info('UE not found')
            return 'UE not found'
        
    return 'Invalid IMSI or IP address'
    


   

