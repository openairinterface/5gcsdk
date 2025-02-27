import threading
import subprocess
import logging
import json
from flask import Flask

# Configure Flask and Logging
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store UE instances
ue_instances = {}

class TrafficUE(threading.Thread):
    def __init__(self, ip, config):
        super().__init__()
        self.ip = ip
        self.debit = config.get("debit")
        self.time = config.get("time")
        self.protocol = config.get("protocol")
        self.interval = config.get("interval")
        self.direction = config.get("direction")
        self.iperf_output = None

    def run(self):
        iperf_command = self.construct_iperf_command()
        if iperf_command:
            try:
                logger.info(f"[UE {self.ip}] Running Iperf3 command: {iperf_command}")
                result = subprocess.run(iperf_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                raw_output = result.stdout.decode().strip()
                try:
                   self.iperf_output = json.loads(raw_output)  
                   logger.info(f"[UE {self.ip}] Iperf3 output successfully parsed.")
                except json.JSONDecodeError:
                   logger.error(f"[UE {self.ip}] Failed to parse JSON output: {raw_output}")
                   self.iperf_output = {"error": "Invalid JSON from iperf3"}
            except subprocess.CalledProcessError as e:
                logger.error(f"[UE {self.ip}] Iperf3 command failed: {str(e)}")
                self.iperf_output = e.output.decode()

    def construct_iperf_command(self):
        """Construct iperf3 command based on UE settings."""
        if not all([self.debit, self.time, self.protocol, self.interval, self.direction]):
            return None

        if self.direction == "UL":
             return f"iperf3 -c {self.ip} -b {self.debit}M -t {self.time} -R -i {self.interval} -J {('-u' if self.protocol == 'UDP' else '')}"
        elif self.direction == "DL":
            return f"iperf3 -c {self.ip} -b {self.debit}M -t {self.time} -i {self.interval} -J {('-u' if self.protocol == 'UDP' else '')}"
        elif self.direction in ["bidir", None]:
            return f"iperf3 -c {self.ip} -b {self.debit}M -t {self.time} -i {self.interval} --bidir -J {('-u' if self.protocol == 'UDP' else '')}"
        else:
            logger.error(f"[UE {self.ip}] Invalid direction: {self.direction}")
            return None
