import os
import subprocess
import logging
import docker

def add_ues(nb_ues):
    """
    Deploys a specified number of User Equipment (UE) containers.
    
    This function deploys the specified number of UE containers given by the client as an argument using Docker Compose.
    It checks the existing containers, and if the number of UEs to deploy is within the range of available UE names, it starts the deployment.
    
    :param nb_ues: The number of UE containers to deploy.
    :type nb_ues: int
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    ues_list = ['oai-nr-ue', 'oai-nr-ue2', 'oai-nr-ue3', 'oai-nr-ue4', 'oai-nr-ue5', 'oai-nr-ue6', 'oai-nr-ue7', 'oai-nr-ue8', 'oai-nr-ue9', 'oai-nr-ue10']
    client = docker.from_env()
    containers = client.containers.list()
    existing_containers=[]
    for container in containers:
        x = container.name
        existing_containers.append(str(x))
    
    if nb_ues > 10: 
        logger.error("Number of UEs out of range.")
        return
    else: 
        try:
            home_dir = os.path.expanduser("~")
            directory = os.path.join(home_dir,'openairinterface5g-develop', 'ci-scripts', 'yaml_files', '5g_rfsimulator')
            os.chdir(directory) 
            i = 0
            j = 0
            while i < nb_ues:
                if ('rfsim5g-'+ str(ues_list[j])) not in existing_containers :
                    subprocess.run(['docker-compose', 'up', '-d', ues_list[j]], check=True)
                    i += 1
                j += 1

                if i == nb_ues:
                    break

            logger.info("{} UE(s) were successfully deployed.".format(nb_ues))

        except subprocess.CalledProcessError as e:
            logger.error("Error occurred while executing command: %s", e)

def remove_ues(nb_ues):
    """
    Removes a specified number of User Equipment (UE) containers.

    This function stops and removes the specified number of UE containers
    using Docker commands. It checks the existing containers and stops and removes
    the UE containers up to the specified number.

    :param nb_ues: The number of UE containers to remove.
    :type nb_ues: int
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    i = 0
    ues_list = ['rfsim5g-oai-nr-ue', 'rfsim5g-oai-nr-ue2', 'rfsim5g-oai-nr-ue3', 'rfsim5g-oai-nr-ue4', 'rfsim5g-oai-nr-ue5', 'rfsim5g-oai-nr-ue6', 'rfsim5g-oai-nr-ue7', 'rfsim5g-oai-nr-ue8', 'rfsim5g-oai-nr-ue9', 'rfsim5g-oai-nr-ue10']
    client = docker.from_env()
    containers = client.containers.list()
    for container in containers:
        if container.name in ues_list and i < nb_ues:
            subprocess.run(['docker', 'stop', str(container.name)], check=True)
            subprocess.run(['docker', 'rm', str(container.name)], check=True)
            i += 1
    if i == 0: 
        logger.info('No UEs exist.')
    elif i < nb_ues:
        logger.info('{} UE(s) was(were) successfully released.'.format(i))
    else:
        logger.info('{} UEs were successfully released'.format(nb_ues))


def start_oai_rfsim5g():
    """
    Starts the OAI RFSIM5G environment.

    This function pulls Docker images required for the OAI RFSIM5G environment and starts the
    necessary Docker containers.

    :return: None
    """
    home_dir = os.path.expanduser("~")
    directory = os.path.join(home_dir,'openairinterface5g-develop', 'ci-scripts', 'yaml_files', '5g_rfsimulator')
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

