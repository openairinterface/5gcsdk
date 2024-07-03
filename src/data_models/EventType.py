from enum import Enum

class EventType(Enum):
    REGISTERED_UES = "RegisteredUEs"
    UE_STATUS = "UEStatus"
    UE_CELL_ID = "UECellID"
    UE_TRAFFIC = "UETraffic"