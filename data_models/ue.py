import time
import uuid
import json 

class UE:
    def __init__(self, imsi, ngapId) -> None:
        self._imsi = imsi
        self._ngapId = ngapId
        self._ips = []
        
    def append_ip(self, ip):
        if not self.has_ip(ip):
            self._ips.append(ip)
        return
    
    def has_ip(self, ip):
        return ip in self._ips
    
    def update_ngap_id(self, ngapid):
        self._ngapId = ngapid
        
    def to_http_response(self, ip):
        return {
            "req_id": str(uuid.uuid1()),
            "ue_ip" : ip,
            "imsi"  : self._imsi,
            "ngap_id": self._ngapId,
            "timestamp": time.time(),
            "ips": self._ips
        }
  
