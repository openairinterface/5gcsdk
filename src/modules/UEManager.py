# SPDX-License-Identifier: MIT

import logging
from pymongo import MongoClient
import re
from enum import Enum
from datetime import datetime
from data_models.ue import UE
from data_models.UEStatus import UEStatus
from data_models.TrafficVolume import TrafficVolume

def get_registered_ues():
    """
    Retrieves registered users from the MongoDB collections.

    This function connects to the MongoDB database and retrieves users from the
    'amf_notifications' collection. It extracts information such as SUPI, RAN UE NGAP ID,
    and RM State for each user.

    :return: A list of UE objects containing user information.
    :rtype: list

    :raises AssertionError: If the required collections are not found or if no documents or reports are found.
    :raises Exception: For any other errors that occur during database operations.

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
        
        registered_ues = [UE(supi=user_info['supi'],
                             ad_ipv4_addr=user_info['adIpv4Addr'],
                             ran_ue_ngap_id=user_info['ran_ue_ngap_id'],
                             rm_state=user_info['rm_state'],
                             timestamp=user_info['timestamp'])
                          for user_info in existing_users.values()]
        
        logger.info("Registered users retrieved successfully.")
        return registered_ues

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
    for item in parts:
        if not item.isdigit() or not 0 <= int(item) <= 255:
            return False
    return True

def _is_valid_imsi(imsi):
    return imsi.startswith("imsi-") and len(imsi) == 20 and imsi[5:].isdigit()

def get_ue_status(ue_credentials):
    """
    This function takes the IMSI (International Mobile Subscriber Identity) or IP Address
    of a UE as input and returns its status if the UE is registered. If the IMSI or IP Address
    is not found in the database, it returns 'UE not found'. If the input is invalid, it returns
    'Invalid IMSI or IP address'.

    :param ue_credentials: The IMSI or IP Address of the UE.
    :type ue_credentials: str
    :return: The status of the UE as an instance of UEStatus.
    :rtype: UEStatus

    :raises AssertionError: If the MongoDB connection fails, the collections are not found, or the IMSI/IP address format is invalid.
    :raises Exception: For any other errors that occur during database operations.

    Usage Example:
    --------------
    >>> imsi = "imsi-123456789012345"
    >>> status = get_ue_status(imsi)
    >>> print(f"Status of UE with IMSI {imsi}: {status.name}")

    >>> ip_address = "192.168.1.1"
    >>> status = get_ue_status(ip_address)
    >>> print(f"Status of UE with IP {ip_address}: {status.name}")
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

        if not (_is_valid_ipv4(ue_credentials) or _is_valid_imsi(ue_credentials)):
            logger.error("Invalid IMSI or IP address format")
            return UEStatus.INVALID_INPUT

        latest_timestamp = 0
        latest_rm_state = None
        imsi = None

        if _is_valid_ipv4(ue_credentials):
            for data_plane in smf_collection.find():
                ue_ip = data_plane['eventNotifs'][0].get('adIpv4Addr')
                if ue_credentials == ue_ip:
                    imsi = 'imsi-' + data_plane['eventNotifs'][0].get('supi')
                    break

            if not imsi:
                logger.info('UE not found')
                return UEStatus.UE_NOT_FOUND

        if _is_valid_imsi(ue_credentials):
            imsi = ue_credentials

        for document in amf_collection.find():
            assert document is not None, "No documents found in amf_notifications collection"
            for report in document["reportList"]:
                assert report is not None, "No reports found in document"
                supi = report["supi"]
                if supi == imsi:
                    if report["timeStamp"] > latest_timestamp:
                        latest_timestamp = report["timeStamp"]
                        latest_rm_state = report["rmInfoList"][0]["rmState"]

        if latest_rm_state == "REGISTERED":
            logger.info(f"Status of UE with IMSI {imsi}: REGISTERED")
            return UEStatus.REGISTERED
        elif latest_rm_state:
            logger.info(f"Status of UE with IMSI {imsi}: DEREGISTERED")
            return UEStatus.DEREGISTERED
        else:
            logger.info('UE not found')
            return UEStatus.UE_NOT_FOUND

    except AssertionError as error:
        logger.error(error)
        return UEStatus.INVALID_INPUT

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return UEStatus.ERROR
    



def get_ue_traffic(start_time, end_time, ue_supi=None):
    """
    Retrieve the total uplink and downlink data usage volumes within a specified time range
    from the MongoDB database.

    This function calculates the total uplink and downlink data volumes by querying the
    'smf_notification_traffic' collection in the 'notification_db' MongoDB database. It filters
    records based on the provided start and end timestamps (in UNIX timestamp format) and optionally
    filters by the UE SUPI (Subscription Permanent Identifier).

    :param start_time: Start timestamp (UNIX timestamp format) or date string (format: 'YYYY-MM-DD HH:MM:SS').
    :type start_time: int or str
    :param end_time: End timestamp (UNIX timestamp format) or date string (format: 'YYYY-MM-DD HH:MM:SS').
    :type end_time: int or str
    :param ue_supi: Optional. UE SUPI (Subscription Permanent Identifier) to filter data usage by a specific UE.
    :type ue_supi: str, optional
    :return: Dictionary containing the total uplink and downlink data volumes.
    :rtype: dict
    :raises AssertionError: If the required MongoDB collections ('smf_notification_traffic' or 'smf_notifications') are not found in the database.
    :raises ValueError: If the date strings provided for start_time or end_time are not in the correct format.
    :raises RuntimeError: If there are any issues in querying the MongoDB database.
    
    Usage Example:
    --------------
    >>> start_time = "2023-01-01 00:00:00"
    >>> end_time = "2023-01-02 00:00:00"
    >>> usage = get_ue_traffic(start_time, end_time)
    >>> print(f"Total Uplink Data: {usage[TrafficVolume.TOTAL_UPLINK]} bytes")
    >>> print(f"Total Downlink Data: {usage[TrafficVolume.TOTAL_DOWNLINK]} bytes")
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Retrieving UE traffic from {start_time} to {end_time} for SUPI: {ue_supi}")

    # Ensure start_time is less than or equal to end_time
    assert start_time <= end_time, "Start time must be less than or equal to end time"
    
    client = MongoClient('mongodb://localhost:27017/')
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    db = client['notification_db']
    
    # Check if required collections exist
    if 'smf_notification_traffic' not in db.list_collection_names():
        raise AssertionError("smf_notification_traffic collection not found in database")
    if 'smf_notifications' not in db.list_collection_names():
        raise AssertionError("smf_notifications collection not found in database")
    
    smf_traffic_collection = db['smf_notification_traffic']
    
    # Determine if start_time and end_time are timestamps or date strings
    if isinstance(start_time, int) and isinstance(end_time, int):
        start_timestamp = start_time
        end_timestamp = end_time
    else:
        try:
            # Convert date strings to timestamps
            start_timestamp = int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp())
        except ValueError as e:
            raise ValueError("Invalid date format. Use 'YYYY-MM-DD HH:MM:SS'.") from e
    
    logger.info(f"Converted start_time: {start_timestamp}, end_time: {end_timestamp}")

    # Create the query filter
    query = {
        'timeStamp': {'$gte': str(start_timestamp), '$lte': str(end_timestamp)}
    }
    
    if ue_supi:
        query['supi'] = ue_supi
    
    logger.info(f"Query: {query}")

    # Retrieve records from the database
    try:
        records = smf_traffic_collection.find(query)
    except Exception as e:
        logger.error(f"Failed to retrieve records from MongoDB: {str(e)}")
        raise RuntimeError(f"Failed to retrieve records from MongoDB: {str(e)}") from e

    total_uplink = 0
    total_downlink = 0
    for record in records:
        usage_report = record.get('customized_data', {}).get('Usage Report', {})
        total_uplink += usage_report.get('Volume', {}).get('Uplink', 0)
        total_downlink += usage_report.get('Volume', {}).get('Downlink', 0)
    
    logger.info(f"Total Uplink: {total_uplink} bytes, Total Downlink: {total_downlink} bytes")

    # Return the results
    return {
        TrafficVolume.TOTAL_UPLINK: total_uplink,
        TrafficVolume.TOTAL_DOWNLINK: total_downlink
    }