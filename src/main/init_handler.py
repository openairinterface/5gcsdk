import os
import yaml
import subprocess
import sys
import psutil
import logging

logging.basicConfig(level=logging.DEBUG)  
logger = logging.getLogger(__name__)

def start_handler():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    status_file_path = os.path.join(current_dir, '../../etc/handler_status.yaml')
    handler_path = os.path.join(current_dir, 'handler.py')

    with open(status_file_path, 'r') as file:
        data = yaml.safe_load(file)

    handler_status = data['handler_status']

    if handler_status == 'off':
        if os.path.isfile(handler_path):
            process = subprocess.Popen([sys.executable, handler_path])
            data['handler_pid'] = process.pid
            data['handler_status'] = 'on'
            with open(status_file_path, 'w') as file:
                yaml.safe_dump(data, file)
            logger.info("Handler process started.")
        else:
            logger.debug("Handler process file not found.")

def stop_handler():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    status_file_path = os.path.join(current_dir, '../../etc/handler_status.yaml')

    try:
        with open(status_file_path, 'r') as file:
            data = yaml.safe_load(file)

        handler_pid = int(data.get('handler_pid'))  

        if handler_pid is not None:
            proc = psutil.Process(handler_pid)
            logger.debug(f"Command line of the process: {proc.cmdline()}")
            logger.info(f"Found handler.py with PID: {handler_pid}. Terminating it..")
            proc.terminate()
            proc.wait(timeout=5)
            data['handler_status'] = 'off'  
            data['handler_pid'] = 'None' 
            with open(status_file_path, 'w') as file:
                yaml.safe_dump(data, file)
            logger.info(f"handler was succesfully detached.")
        else:
            logger.info("No handler process running.")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        logger.error(f"Failed to terminate handler.py: {e}")

