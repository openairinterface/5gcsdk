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

    Usage Example:
    --------------
    >>> registered_ues = get_registered_ues()
    >>> for ue in registered_ues:
    >>>     print(ue)
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        client = MongoClient('mongodb://localhost:27017/')
        logging.getLogger('pymongo').setLevel(logging.WARNING)
        
        db = client['notification_db']
        assert 'amf_notifications' in db.list_collection_names(), "amf_notifications collection not found"
        assert 'smf_notifications' in db.list_collection_names(), "smf_notifications collection not found"
        
        amf_collection = db['amf_notifications']
        smf_collection = db['smf_notifications']
        existing_users = {}
        
        for document in amf_collection.find():
            assert document is not None, "No documents found in amf_notifications collection"
            for report in document["reportList"]:
                assert report is not None, "No reports found in document"
                supi = report["supi"]
                ran_ue_ngap_id = report["ranUeNgapId"]
                rm_state = report["rmInfoList"][0]["rmState"]
                timestamp = report["timeStamp"]
                ip_addr = None
                
                for data_plane in smf_collection.find():
                    smf_supi = 'imsi-' + data_plane['eventNotifs'][0].get('supi')
                    if smf_supi == supi:
                        ip_addr = data_plane['eventNotifs'][0].get('adIpv4Addr')
                        break
                
                if supi in existing_users:
                    if timestamp > existing_users[supi]['timestamp']:
                        existing_users[supi] = {'supi': supi, 'adIpv4Addr': ip_addr, 'ran_ue_ngap_id': ran_ue_ngap_id,
                                                'rm_state': rm_state, 'timestamp': timestamp}
                else:
                    existing_users[supi] = {'supi': supi, 'adIpv4Addr': ip_addr, 'ran_ue_ngap_id': ran_ue_ngap_id,
                                            'rm_state': rm_state, 'timestamp': timestamp}
        
        keys_to_remove = []
        
        for supi, user_info in existing_users.items():
            if user_info['rm_state'] != "REGISTERED":
                keys_to_remove.append(supi)
        
        for key in keys_to_remove:
            existing_users.pop(key)
        
        logger.info("Registered users retrieved successfully.")
        return existing_users

    except AssertionError as error:
        logger.error(error)
        return []

    except Exception as e:
        logger.error("An error occurred: %s", e)
        return []

def _is_valid_ipv4(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        if not 0 <= int(part) <= 255:
            return False
    return True

def _is_valid_imsi(imsi):
    return imsi.startswith('imsi-') and imsi[5:].isdigit() and len(imsi[5:]) == 15

def get_ue_status(ue_credentials):
    """
    This function takes the IMSI (International Mobile Subscriber Identity) or IP Address
    of a UE as input and returns its status if the UE is registered. If the IMSI or IP Address
    is not found in the database, it returns 'UE not found'. If the input is invalid, it returns
    'Invalid IMSI or IP address'.

    :param ue_credentials: The IMSI or IP Address of the UE.
    :type ue_credentials: str
    :return: The status of the UE, 'UE not found' if the IMSI or IP Address is not found, or
             'Invalid IMSI or IP address' if the input is invalid.
    :rtype: str
    
    Usage Example:
    --------------
    >>> imsi = "imsi-123456789012345"
    >>> status = get_ue_status(imsi)
    >>> print(f"Status of UE with IMSI {imsi}: {status}")

    >>> ip_address = "192.168.1.1"
    >>> status = get_ue_status(ip_address)
    >>> print(f"Status of UE with IP {ip_address}: {status}")
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    try:
        client = MongoClient('mongodb://localhost:27017/')
        assert client is not None, "Failed to connect to MongoDB"
        
        db = client['notification_db']
        assert 'amf_notifications' in db.list_collection_names(), "amf_notifications collection not found"
        assert 'smf_notifications' in db.list_collection_names(), "smf_notifications collection not found"
        
        amf_collection = db['amf_notifications']
        smf_collection = db['smf_notifications']

        assert _is_valid_ipv4(ue_credentials) or _is_valid_imsi(ue_credentials), "Invalid IMSI or IP address format"

        if _is_valid_ipv4(ue_credentials):
            latest_timestamp = 0
            latest_rm_state = None
            imsi = None

            for data_plane in smf_collection.find():
                ue_ip = data_plane['eventNotifs'][0].get('adIpv4Addr')
                if ue_credentials == ue_ip:
                    imsi = 'imsi-' + data_plane['eventNotifs'][0].get('supi')
                    break

            if imsi:
                for document in amf_collection.find():
                    assert document is not None, "No documents found in amf_notifications collection"
                    for report in document["reportList"]:
                        assert report is not None, "No reports found in document"
                        supi = report["supi"]
                        if supi == imsi:
                            if report["timeStamp"] > latest_timestamp:
                                latest_timestamp = report["timeStamp"]
                                latest_rm_state = report["rmInfoList"][0]["rmState"]

                if latest_rm_state:
                    logger.info(f"Status of UE with IP {ue_credentials}: {latest_rm_state}")
                    return latest_rm_state
                else:
                    logger.info('UE not found')
                    return 'UE not found'
            else:
                logger.info('UE not found')
                return 'UE not found'

        if _is_valid_imsi(ue_credentials):
            latest_timestamp = 0
            latest_rm_state = None

            for document in amf_collection.find():
                assert document is not None, "No documents found in amf_notifications collection"
                for report in document["reportList"]:
                    assert report is not None, "No reports found in document"
                    supi = report["supi"]
                    if supi == ue_credentials:
                        if report["timeStamp"] > latest_timestamp:
                            latest_timestamp = report["timeStamp"]
                            latest_rm_state = report["rmInfoList"][0]["rmState"]

            if latest_rm_state:
                logger.info(f"Status of UE with IMSI {ue_credentials}: {latest_rm_state}")
                return latest_rm_state
            else:
                logger.info('UE not found')
                return 'UE not found'

    except AssertionError as error:
        logger.error(error)
        return 'Invalid IMSI or IP address'

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 'Error occurred while retrieving UE status'
