"""
oai5gc SDK

This module represents the oai5gc SDK, which is a comprehensive toolkit for interacting with various components
of the 5G Core Network (5GC) developed by OpenAirInterface (OAI). It provides a set of functionalities to manage
and control different aspects of the 5GC, including user equipment (UE) management, network function (NF)
management, event callbacks, and more.

Packages:
- RFsimUEManager: Provides functionalities for managing simulated UEs in the RF environment.
- UEManager: Offers functionalities for managing UEs within the 5GC network.
- CallbackManager: Facilitates the registration and handling of event callbacks.
- NFManager: Provides functionalities for managing network functions (NFs) within the 5GC.

Usage:
1. Start the handler.py script to set up the Flask web application for handling AMF and SMF notifications.
1. Import the `oai5gc` module.
3. Start the OAI RFSIM5G environment using the `START_OAI_RFSIM5G` function.
2. Utilize the functionalities provided by the respective packages within the SDK.

"""
import sys
import os
import subprocess

# Get the current directory and parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to the system path to import modules
sys.path.append(os.path.join(parent_dir, 'modules'))

from RFsimUEManager import *
from UEManager import *
from CallbackManager import *
from NFManager import *

def start_handler():
    handler_path = os.path.join(current_dir, 'handler.py')
    if os.path.isfile(handler_path):
        subprocess.Popen([sys.executable, handler_path])

start_handler()


 



