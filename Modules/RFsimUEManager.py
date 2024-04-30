import docker
import os
import subprocess



def add_UEs( nb_UES):
        """
        Deploys a specified number of User Equipment (UE) containers.

        This function deploys the specified number of UE containers using Docker Compose.
        It checks the existing containers, and if the number of UEs to deploy is within
        the range of available UE names, it starts the deployment.

        :param nb_UES: The number of UE containers to deploy.
        :type nb_UES: int
        """
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
        if i==0 : 
            return print('No UEs exist.')
        if i < nb_UES : 
            return print('{} UE(s) was(were) successfully released.'.format(i))

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