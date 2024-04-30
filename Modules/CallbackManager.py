import time
from pymongo import MongoClient
from Modules.UEManager import get_registered_UEs

def registerCallBackUEStatus(imsi, callback_function=None, *arguments):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']
    amf_collection = db['amf_notifications']
    latest_ue_info = {}  # Dictionary to store information of UEs with latest timestamp
    print("imsi",imsi)
    if callback_function==None:
        while True:
            temp_ue_info = {}  # Temporary dictionary to store updated UE information
            # Retrieve information of all UEs
            for document in amf_collection.find():
                for report in document["reportList"]:
                    supi = report["supi"]
                    ran_ue_ngap_id_amf = report["ranUeNgapId"]
                    rm_state_amf = report["rmInfoList"][0]["rmState"]
                    timestamp = report["timeStamp"]

                        # Check if UE already exists in dictionary or if timestamp is newer
                    if supi not in temp_ue_info or timestamp > temp_ue_info[supi]['timestamp_amf']:
                            # Update UE information in the temporary dictionary
                        temp_ue_info[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                                'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

                # Check if there's any change in UE information
            if temp_ue_info != latest_ue_info and imsi in temp_ue_info:
                latest_ue_info = temp_ue_info
                return True
            else:
                return False


    if callback_function!=None:
        first_capture = False  # Flag to indicate if this is the first capture

        while True:
            temp_ue_info = {}  # Temporary dictionary to store updated UE information

            # Retrieve information of all UEs
            for document in amf_collection.find():
                for report in document["reportList"]:
                    supi = report["supi"]
                    ran_ue_ngap_id_amf = report["ranUeNgapId"]
                    rm_state_amf = report["rmInfoList"][0]["rmState"]
                    timestamp = report["timeStamp"]

                    # Check if UE already exists in dictionary or if timestamp is newer
                    if supi not in temp_ue_info or timestamp > temp_ue_info[supi]['timestamp_amf']:
                        # Update UE information in the temporary dictionary
                        temp_ue_info[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf,
                                            'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

            # Check if there's any change in UE information
            if temp_ue_info != latest_ue_info and imsi in temp_ue_info:
                latest_ue_info = temp_ue_info
                
                # Trigger callback only if this is not the first capture
                if first_capture:
                    callback_function(*arguments)
                else:
                    first_capture = True
                    
                time.sleep(3)


def registerCallbackUE(imsi, callback_function=None, *arguments):

        """
        Callback function to check if a specific IMSI is registered.

        This function takes another function as an argument, which retrieves the
        registered users. It checks if the specified IMSI is registered, and if so,
        it calls the callback function and returns True.

        :param imsi: The IMSI to check registration for.
        :type imsi: str
        :param callback_function: The function to call when the IMSI is registered.
        :type callback_function: function
        :return: True if the IMSI is registered, otherwise False.
        :rtype: bool
        """
        registered_users = get_registered_UEs()  

        if callback_function==None:

                if imsi in registered_users:
                    return True
                else:
                    return False
            
        if callback_function!=None:

            while True:
                registered_users = get_registered_UEs()  
                
                if imsi in registered_users:
                    callback_function(*arguments)
                    time.sleep(3)
    
