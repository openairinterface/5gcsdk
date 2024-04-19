"""
This module represents an SDK related to THE 5G Core Network.
"""
from pymongo import MongoClient
import yaml
import uuid
import requests
import os
import subprocess
from datetime import datetime
import docker 
import time
import requests

def get_registered_UEs():
    """
    Retrieves registered users from the MongoDB collections.

    This function connects to the MongoDB database and retrieves users from the
    'amf_notifications' collection. It extracts information such as SUPI, RAN UE NGAP ID,
    and RM State for each user.

    :return: A list of dictionaries containing user information.
    :rtype: list
    """

    client = MongoClient('mongodb://localhost:27017/')  
    db = client['notification_db']
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

    # Convert the dictionary of users to a list and return it
    return list(existing_users.values())



def registerNF(NF,ip):
    """
        Registers a Network Function (NF) with its corresponding IP address.

        This function updates the configuration file with the IP address of the
        specified NF (AMF or SMF) and creates a subscription for receiving notifications
        related to the NF.

        :param NF: The type of Network Function (AMF or SMF).
        :type NF: str
        :param ip: The IP address of the Network Function.
        :type ip: str
        :return: A message indicating whether the registration was successful.
        :rtype: str
    """

    file_path = '/home/achraf/Downloads/ue-identity-service-master/etc/config.yaml'
    if NF not in['SMF','AMF'] :
        return print("ERROR: there is no network function that matches {}".format(NF))
    
    if NF=='AMF':
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)

        config['amf']['ip'] = ip

        with open(file_path, 'w') as file:
            yaml.dump(config, file)
        ip_addr = config['sbi']['ip']
        port = config['sbi']['port']
        sub_endpoint = f"http://{config['amf']['ip']}:{config['amf']['port']}{config['amf']['baseUrl']}/subscriptions"
        sub_body = {
                    "subscription": {
                        "eventList": [
                            {
                                "type": "REGISTRATION_STATE_REPORT"
                            }
                        ],
                        "eventNotifyUri": f"{ip_addr}:{port}/callbacks/amf-reports",
                        "notifyCorrelationId": str(uuid.uuid1()),
                        "nfId": str(uuid.uuid1())
                    }
                }
        try:
            r = requests.post(url =sub_endpoint, json=sub_body)
            if(r.status_code == 201):
                return print("{}({}) was successfully created.".format(NF,ip))
    
            else:
                return ""
        except:
            return ""
        
        
    if NF=='SMF' :
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)

        config['smf']['ip'] = ip

        with open(file_path, 'w') as file:
            yaml.dump(config, file)

        ip_addr = config['sbi']['ip']
        port = config['sbi']['port'] 
        sub_endpoint = f"http://{config['smf']['ip']}:{config['smf']['port']}{config['smf']['baseUrl']}/subscriptions"
        sub_body ={
            "anyUeInd": True,
            "groupId": "aEb1CD9b-561-97-2cbA7bEc2eAC07ECb6",
            "pduSeId": 1,
            "dnn": "oai",
            "notifId": str(uuid.uuid1()),
            "notifUri": f"{ip_addr}:{port}/callbacks/dataplane-reports",
            "altNotifIpv4Addrs": [
                ip_addr
            ],
            "altNotifIpv6Addrs": [
                "fe80::14e0:6d4a:928e:628c"
            ],
            "altNotifFqdns": [
                "string"
            ],
            "eventSubs": [
                {
                "event": "PDU_SES_EST"
                }
            ],
            "eventNotifs": [
                {
                "event": "PDU_SES_EST",
                "timeStamp": str(datetime.utcnow().isoformat()[:-3])+'Z'
                }
            ]
        }

        sub_id = None
        try:
            r = requests.post(url =sub_endpoint, json=sub_body)
            if(r.status_code == 201):
                return print("{}({}) was successfully created.".format(NF,ip))
            else:
                return ""
        except:
            return ""
            
# Example usage:
#nf= 'AMF'
#new_ip_address = '192.168.71.132'  # Example new IP address
#registerNF(nf,new_ip_address)

def add_UEs(nb_UES):
    """
    Deploys a specified number of User Equipment (UE) containers.

    This function deploys the specified number of UE containers using Docker Compose.
    It checks the existing containers, and if the number of UEs to deploy is within
    the range of available UE names, it starts the deployment.

    :param nb_UES: The number of UE containers to deploy.
    :type nb_UES: int
    """
    # Function implementation
    UEs_list = ['oai-nr-ue', 'oai-nr-ue2', 'oai-nr-ue3', 'oai-nr-ue4', 'oai-nr-ue5', 'oai-nr-ue6', 'oai-nr-ue7', 'oai-nr-ue8', 'oai-nr-ue9', 'oai-nr-ue10']
    client = docker.from_env()
    containers = client.containers.list()
    existing_containers=[]
    for container in containers:
        X= container.name
        existing_containers.append(str(X))

    if nb_UES > 10: 
        return print("ERROR: number of UEs out of range.")
    else: 
        try:
            directory = '/home/achraf/Downloads/openairinterface5g-develop/ci-scripts/yaml_files/5g_rfsimulator'
            os.chdir(directory) 
            i = 0
            j = 0
            while i < nb_UES:
                # Run the docker-compose command

                if ('rfsim5g-'+ str(UEs_list[j])) not in existing_containers :
                    subprocess.run(['docker-compose', 'up', '-d',UEs_list[j]], check=True)
                    i += 1
                j += 1

                if i == nb_UES:
                    break 

            print("{} UE(s) were successfully deployed.".format(nb_UES))

        except subprocess.CalledProcessError as e:
            print("Error occurred while executing command:", e)


# Example usage:
#add_UEs(2)


def rm_UEs(nb_UES):
    """
        Removes a specified number of User Equipment (UE) containers.

        This function stops and removes the specified number of UE containers
        using Docker commands. It checks the existing containers and stops/removes
        the UE containers up to the specified number.

        :param nb_UES: The number of UE containers to remove.
        :type nb_UES: int
    """    
    i=0
    UEs_list =['rfsim5g-oai-nr-ue','rfsim5g-oai-nr-ue2','rfsim5g-oai-nr-ue3','rfsim5g-oai-nr-ue4','rfsim5g-oai-nr-ue5','rfsim5g-oai-nr-ue6','rfsim5g-oai-nr-ue7','rfsim5g-oai-nr-ue8','rfsim5g-oai-nr-ue9','rfsim5g-oai-nr-ue10']
    client= docker.from_env()
    containers = client.containers.list()
    for container in containers :

        if container.name in UEs_list and i< nb_UES :
            subprocess.run(['docker', 'stop', str(container.name) ], check=True)
            subprocess.run(['docker', 'rm', str(container.name) ], check=True)
        i+=1

    if i < nb_UES : 
        return print('Only {} UEs exist and they were successfully released.'.format(i))
    
    return print('{} UEs were successfully released'.format(nb_UES))

def START_OAI_RFSIM5G():
    directory = '/home/achraf/Downloads/openairinterface5g-develop/ci-scripts/yaml_files/5g_rfsimulator'
    os.chdir(directory) 
    commands = [
        "docker pull mysql:8.0",
        "docker pull oaisoftwarealliance/oai-amf:v2.0.0",
        "docker pull oaisoftwarealliance/oai-smf:v2.0.0",
        "docker pull oaisoftwarealliance/oai-upf:v2.0.0",
        "docker pull oaisoftwarealliance/trf-gen-cn5g:focal",
        "docker pull oaisoftwarealliance/oai-gnb:develop",
        "docker pull oaisoftwarealliance/oai-nr-ue:develop",
        "docker-compose up -d mysql oai-amf oai-smf oai-upf oai-ext-dn"
    ]

    for command in commands:
        subprocess.run(command, shell=True)

# Call the function to execute the Docker commands
#START_OAI_RFSIM5G()

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


# Example usage:
###imsi = 'imsi-208990100001100'
#status = get_ue_status_by_imsi(imsi)
#print(f"Status of UE with IMSI {imsi}: {status}")

#client = MongoClient('mongodb://localhost:27017/')
#db = client['notification_db']

# Print content of amf_notifications collection
#print("Content of amf_notifications collection:")
#for doc in db['amf_notifications'].find():
 #   print(doc)


def registerCallBackRegisteredUEs():
    """
    Retrieves registered users from the MongoDB collections continuously for 5 minutes.

    This function connects to the MongoDB database and retrieves users from the
    'amf_notifications' collection. It extracts information such as SUPI, RAN UE NGAP ID,
    and RM State for each user.

    :return: None
    """

    client = MongoClient('mongodb://localhost:27017/')  
    db = client['notification_db']
    amf_collection = db['amf_notifications']
   
    prev_existing_users = {}  # Store the previous state of existing users
    start_time = time.time()  # Record the start time
    current_time = datetime.now()
    while time.time() - start_time < 300:  # Exit loop after 5 minutes (300 seconds)
        existing_users = {}

        for document in amf_collection.find():
            for report in document["reportList"]:
                supi = report["supi"]
                ran_ue_ngap_id_amf = report["ranUeNgapId"]
                rm_state_amf = report["rmInfoList"][0]["rmState"]
                timestamp = report["timeStamp"]

                # Check if the user is registered
                if rm_state_amf == "REGISTERED":
                    # Check if the user is already in the dictionary
                    if supi in existing_users:
                        # If the current notification has a newer timestamp, update the information
                        if timestamp > existing_users[supi]['timestamp_amf']:
                            existing_users[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf, 'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}
                    else:
                        # If the user is not in the dictionary, add them
                        existing_users[supi] = {'supi': supi, 'ranUeNgapId_amf': ran_ue_ngap_id_amf, 'rmState_amf': rm_state_amf, 'timestamp_amf': timestamp}

        # Create a list to store users to remove
        users_to_remove = []

        # Check for deregistered users and mark them for removal
        for supi, user_info in existing_users.items():
            for document in amf_collection.find():
                for report in document["reportList"]:
                    if report["supi"] == supi:
                        # Check if the user has a DEREGISTERED state and a newer timestamp
                        if report["rmInfoList"][0]["rmState"] == "DEREGISTERED" and report["timeStamp"] > user_info["timestamp_amf"]:
                            # Mark the user for removal
                            users_to_remove.append(supi)
                            break  # No need to check other reports for this user

        # Remove the marked users
        for supi in users_to_remove:
            existing_users.pop(supi)

        # Check if the dictionary has been updated
        if existing_users != prev_existing_users:
            # Print the registered users
            print("################################################ {} ########################################### \n".format(current_time))            
            for user_info in existing_users.values():
                print("  ",user_info , "\n")
            prev_existing_users = existing_users  # Update the previous state                                      

    print("Exiting after 5 minutes.")

# Call the function to start retrieving users continuously
#registerCallBackRegisteredUEs()




def registerCallBackUEStatus():
    """
    Retrieves and prints existing UE information with the latest timestamp from the MongoDB collection.
    
    This function connects to the MongoDB database and retrieves UE information
    from the 'amf_notifications' collection. It prints the information for each UE
    with the latest timestamp in dictionary format.
    
    :return: None
    """
    # Connect to the MongoDB database
    client = MongoClient('mongodb://localhost:27017/')
    db = client['notification_db']
    amf_collection = db['amf_notifications']

    # Dictionary to store information of UEs with latest timestamp
    latest_ue_info = {}    
    start_time = time.time()  # Record the start time
    current_time = datetime.now()
    
    while time.time() - start_time < 300:
        # Temporary dictionary to store updated UE information
        temp_ue_info = {}
        
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
        if temp_ue_info != latest_ue_info:
            # Print information for each UE with latest timestamp in dictionary format
            print("################################################ {} ########################################### \n".format(current_time))            
            for ue_info in temp_ue_info.values():
                print("  " ,ue_info , "\n")
                
            # Update latest_ue_info with the new information
            latest_ue_info = temp_ue_info



#registerCallBackUEStatus()


def run_iperf_server(container_name='nr-ue', local_address='12.1.1.2', port=5001):
    """
    Run an iperf server inside a Docker container.

    :param container_name: The name or ID of the Docker container.
    :param local_address: The local address to bind the iperf server to (default is '12.1.1.2').
    :param port: The port number for the iperf server (default is 5001).
    :return: None
    """
    directory = '/home/achraf/Downloads/openairinterface5g-develop/ci-scripts/yaml_files/5g_rfsimulator'
    os.chdir(directory) 
    command = f"docker exec -it {container_name} /bin/bash -c 'iperf -B {local_address} -u -i 1 -s'"
    subprocess.run(command, shell=True)

# Example usage:
#run_iperf_server("rfsim5g-oai-nr-ue")
