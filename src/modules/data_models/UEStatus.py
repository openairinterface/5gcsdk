# SPDX-License-Identifier: MIT

from enum import Enum

class UEStatus(Enum):
    REGISTERED = "REGISTERED"
    DEREGISTERED = "DEREGISTERED"
    UE_NOT_FOUND = "UE not found"
    INVALID_INPUT = "Invalid IMSI or IP address"
    ERROR = "Error occurred while retrieving UE status"