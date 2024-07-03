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
    
    Usage Example:
    --------------
    >>> add_ues(3)
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logging.getLogger("docker.utils.config").setLevel(logging.WARN)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARN)

    # Assertions to prevent crashes
    assert isinstance(nb_ues, int), "nb_ues must be an integer"
    assert 0 < nb_ues <= 10, "nb_ues must be between 1 and 10 inclusive"

    ues_list = ['oai-nr-ue', 'oai-nr-ue2', 'oai-nr-ue3', 'oai-nr-ue4', 'oai-nr-ue5', 'oai-nr-ue6', 'oai-nr-ue7', 'oai-nr-ue8', 'oai-nr-ue9', 'oai-nr-ue10']
    client = docker.from_env()
    containers = client.containers.list()
    existing_containers = [str(container.name) for container in containers]
    
    try:
        home_dir = os.path.expanduser("~")
        directory = os.path.join(home_dir, 'openairinterface5g-develop', 'ci-scripts', 'yaml_files', '5g_rfsimulator')
        assert os.path.isdir(directory), "The required directory does not exist"
        os.chdir(directory)
        
        i = 0
        j = 0
        while i < nb_ues:
            if ('rfsim5g-' + str(ues_list[j])) not in existing_containers:
                subprocess.run(['docker-compose', 'up', '-d', ues_list[j]], check=True)
                i += 1
            j += 1

            if i == nb_ues:
                break

        logger.info("{} UE(s) were successfully deployed.".format(nb_ues))

    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while executing command: %s", e)

    except AssertionError as error:
        logger.error(error)

def remove_ues(nb_ues):
    """
    Removes a specified number of User Equipment (UE) containers.

    This function stops and removes the specified number of UE containers
    using Docker commands. It checks the existing containers and stops and removes
    the UE containers up to the specified number.

    :param nb_ues: The number of UE containers to remove.
    :type nb_ues: int
    
    Usage Example:
    --------------
    >>> remove_ues(2)
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logging.getLogger("docker.utils.config").setLevel(logging.WARN)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARN)

    # Assertions to prevent crashes
    assert isinstance(nb_ues, int), "nb_ues must be an integer"
    assert 0 < nb_ues <= 10, "nb_ues must be between 1 and 10 inclusive"

    ues_list = ['rfsim5g-oai-nr-ue', 'rfsim5g-oai-nr-ue2', 'rfsim5g-oai-nr-ue3', 'rfsim5g-oai-nr-ue4', 'rfsim5g-oai-nr-ue5', 'rfsim5g-oai-nr-ue6', 'rfsim5g-oai-nr-ue7', 'rfsim5g-oai-nr-ue8', 'rfsim5g-oai-nr-ue9', 'rfsim5g-oai-nr-ue10']
    client = docker.from_env()
    containers = client.containers.list()
    
    try:
        i = 0
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
            logger.info('{} UEs were successfully released.'.format(nb_ues))

    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while executing command: %s", e)

    except AssertionError as error:
        logger.error(error)


