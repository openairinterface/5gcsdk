# SPDX-License-Identifier: MIT

import os
import socket
import yaml
import subprocess
import sys
import psutil
import logging
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'modules'))
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from CallbackManager import unregister_callback_ue

HANDLER_SCRIPT = 'handler.py'


def _paths():
    """Return (status_file, configuration_file, handler_script) absolute paths."""
    here = os.path.dirname(os.path.abspath(__file__))
    return (
        os.path.join(here, '../../etc/handler_status.yaml'),
        os.path.join(here, '../../etc/configuration.yaml'),
        os.path.join(here, HANDLER_SCRIPT),
    )


def _read_status(status_file_path):
    with open(status_file_path, 'r') as file:
        return yaml.safe_load(file) or {}


def _write_status(status_file_path, data):
    with open(status_file_path, 'w') as file:
        yaml.safe_dump(data, file)


def _mark_stopped(status_file_path, data=None):
    """Reset the status file to the 'no handler running' state."""
    data = dict(data or {})
    data['handler_status'] = 'off'
    data['handler_pid'] = 'None'
    _write_status(status_file_path, data)


def _recorded_pid(data):
    """Read the PID out of the status file, tolerating None/'None'/garbage."""
    pid = data.get('handler_pid')
    if pid in (None, 'None', ''):
        return None
    try:
        return int(pid)
    except (TypeError, ValueError):
        logger.warning("Ignoring malformed handler_pid in status file: %r", pid)
        return None


def _handler_process(pid):
    """
    Return the psutil.Process for pid, but only if it is alive AND is actually our
    handler. Returns None otherwise.

    The cmdline check guards against PID reuse: a stale status file can name a PID
    that the OS has since handed to an unrelated process.
    """
    if pid is None:
        return None
    try:
        proc = psutil.Process(pid)
        if not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE:
            return None
        if not any(HANDLER_SCRIPT in arg for arg in proc.cmdline()):
            logger.warning(
                "PID %s is alive but is not %s (cmdline: %s). Treating as stale.",
                pid, HANDLER_SCRIPT, proc.cmdline())
            return None
        return proc
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def start_handler():
    """
    Start handler.py as a detached process and record it in etc/handler_status.yaml.

    If the status file claims a handler is running but the recorded process is gone
    (a crash, a kill -9, or a stop_handler() that did not complete), the stale state
    is reported and recovered from rather than silently skipping the start.

    :raises RuntimeError: if a handler really is already running.
    :raises FileNotFoundError: if handler.py cannot be found.
    """
    status_file_path, _, handler_path = _paths()

    data = _read_status(status_file_path)
    pid = _recorded_pid(data)
    proc = _handler_process(pid)

    if data.get('handler_status') != 'off':
        if proc is not None:
            raise RuntimeError(
                f"A handler is already running (PID {pid}). Call stop_handler() before "
                f"starting a new one.")
        logger.warning(
            "handler_status was '%s' but no live handler process was found (recorded PID: %s). "
            "Recovering from stale state and starting a new handler.",
            data.get('handler_status'), data.get('handler_pid'))

    if not os.path.isfile(handler_path):
        raise FileNotFoundError(f"Handler process file not found: {handler_path}")

    process = subprocess.Popen([sys.executable, handler_path])
    data['handler_pid'] = process.pid
    data['handler_status'] = 'on'
    _write_status(status_file_path, data)
    logger.info("Handler process started (PID %s).", process.pid)


def stop_handler():
    """
    Terminate the handler and clear etc/handler_status.yaml.

    Terminating sends SIGTERM, which the handler traps in order to delete its AMF/SMF
    subscriptions on the way out. The status file is reset unconditionally, so a
    handler that already died cannot leave behind a stale 'on' that would block the
    next start_handler().
    """
    status_file_path, _, _ = _paths()

    try:
        data = _read_status(status_file_path)
    except OSError as error:
        logger.error("Could not read handler status file: %s", error)
        return

    pid = _recorded_pid(data)
    proc = _handler_process(pid)

    if proc is None:
        logger.info(
            "No running handler found (recorded PID: %s). Clearing handler status.",
            data.get('handler_pid'))
        _mark_stopped(status_file_path, data)
        return

    try:
        unregister_callback_ue()
    except Exception as error:
        logger.error("Failed to unregister callbacks: %s", error)

    try:
        logger.debug("Command line of the process: %s", proc.cmdline())
        logger.info("Found %s with PID: %s. Terminating it..", HANDLER_SCRIPT, pid)
        proc.terminate()
        proc.wait(timeout=5)
        logger.info("Handler was successfully detached.")
    except psutil.TimeoutExpired:
        logger.warning("Handler PID %s did not exit within 5s. Killing it.", pid)
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception as error:
            logger.error("Failed to kill handler.py: %s", error)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as error:
        logger.error("Failed to terminate handler.py: %s", error)
    finally:
        # Always clear the status file, whatever happened above.
        _mark_stopped(status_file_path, data)


def check_handler_ready(timeout=2):
    """
    Verify that the handler is up and serving, and fail loudly if it is not.

    Intended as a fail-fast gate right after start_handler(). Being able to connect
    is a meaningful signal, not just a liveness check: handler.py creates its AMF and
    SMF subscriptions at import time and exits before serving if any of them fail, so
    an open port means the subscriptions were accepted.

    :param timeout: TCP connect timeout in seconds.
    :raises AssertionError: if the handler is not running or not accepting connections.
    """
    status_file_path, config_file_path, _ = _paths()

    data = _read_status(status_file_path)
    pid = _recorded_pid(data)

    if _handler_process(pid) is None:
        raise AssertionError(
            f"Handler process is not running (handler_status: {data.get('handler_status')}, "
            f"recorded PID: {data.get('handler_pid')}). It most likely exited while "
            f"subscribing - check that MongoDB is up and that the AMF and SMF are reachable "
            f"at the addresses in etc/configuration.yaml.")

    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)
    addr = config['sbi']['ip']
    port = int(config['sbi']['port'])

    try:
        with socket.create_connection((addr, port), timeout=float(timeout)):
            pass
    except OSError as error:
        raise AssertionError(
            f"Handler (PID {pid}) is not accepting connections on {addr}:{port}: {error}")

    logger.info("Handler is ready on %s:%s (PID %s).", addr, port, pid)
    return True
