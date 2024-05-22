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

from Modules.RFsimUEManager import *
from Modules.UEManager import *
from Modules.CallbackManager import *
from Modules.NFManager import *





