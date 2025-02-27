from flask import Flask, request, jsonify
import subprocess
import logging
import numpy as np
import time
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store iperf logs
iperf_logs = []


def generate_time_intervals(distribution_type, total_duration, mean_interval, stddev_interval_or_lambda):
    """
    Generates time intervals based on the chosen distribution (Gaussian or Poisson).
    """
    assert distribution_type in ['gaussian', 'poisson'], "Invalid distribution type. Must be 'gaussian' or 'poisson'."
    assert total_duration > 0, "Total duration must be positive."
    assert mean_interval > 0, "Mean interval must be positive."

    num_intervals = int(total_duration // mean_interval)
    if num_intervals <= 0:
        raise ValueError("Number of intervals must be greater than zero.")

    if distribution_type == 'gaussian':
        intervals = np.random.normal(loc=mean_interval, scale=stddev_interval_or_lambda, size=num_intervals)
        intervals = np.clip(intervals, 0, None)  # Ensure no negative intervals
    elif distribution_type == 'poisson':
        intervals = np.random.poisson(lam=mean_interval, size=num_intervals)

    return intervals


def generate_bandwidth_distribution(distribution_type, total_bandwidth, num_intervals, mean_bandwidth, stddev_bandwidth_or_lambda):
    """
    Generates bandwidth values based on the chosen distribution (Gaussian or Poisson).
    """
    assert distribution_type in ['gaussian', 'poisson'], "Invalid distribution type. Must be 'gaussian' or 'poisson'."
    assert total_bandwidth > 0, "Total bandwidth must be positive."
    assert mean_bandwidth > 0, "Mean bandwidth must be positive."
    assert num_intervals > 0, "Number of intervals must be positive."

    if distribution_type == 'gaussian':
        bandwidths = np.random.normal(loc=mean_bandwidth, scale=stddev_bandwidth_or_lambda, size=num_intervals)
        bandwidths = np.clip(bandwidths, 0, None)  # Ensure no negative bandwidths
    elif distribution_type == 'poisson':
        bandwidths = np.random.poisson(lam=mean_bandwidth, size=num_intervals)

    total_bandwidth_assigned = np.sum(bandwidths)
    if total_bandwidth_assigned > 0:
        scaling_factor = total_bandwidth / total_bandwidth_assigned
        bandwidths = bandwidths.astype(np.float64)
        bandwidths *= scaling_factor

    return bandwidths


@app.route('/run_iperf', methods=['POST'])
def run_iperf():
    try:
        data = request.json
        if not data:
            raise ValueError("Request body is required.")
        
        required_keys = [
            "ip", "distribution_type", "total_duration", "mean_interval", 
            "stddev_interval_or_lambda", "total_bandwidth", "mean_bandwidth", 
            "stddev_bandwidth_or_lambda"
        ]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")

        ip = data["ip"]
        distribution_type = data["distribution_type"]
        total_duration = float(data["total_duration"])
        mean_interval = float(data["mean_interval"])
        stddev_interval_or_lambda = float(data["stddev_interval_or_lambda"])
        total_bandwidth = float(data["total_bandwidth"])
        mean_bandwidth = float(data["mean_bandwidth"])
        stddev_bandwidth_or_lambda = float(data["stddev_bandwidth_or_lambda"])
        on_off = float(data.get("on_off", 0))

        if on_off < 0 or on_off > 100:
            raise ValueError("On-off percentage must be between 0 and 100.")

        off_time = (total_duration * on_off) / 100
        total_duration -= off_time

        intervals = generate_time_intervals(distribution_type, total_duration, mean_interval, stddev_interval_or_lambda)
        bandwidths = generate_bandwidth_distribution(distribution_type, total_bandwidth, len(intervals), mean_bandwidth, stddev_bandwidth_or_lambda)

        elapsed_time = 0
        if off_time > 0:
            logger.info(f"Sleeping for off time: {off_time:.2f} seconds...")
            time.sleep(off_time)

        for interval, bandwidth in zip(intervals, bandwidths):
            iperf_command = f"iperf3 -c {ip} -p 5000 -b {bandwidth}M --json"
            try:
                result = subprocess.run(iperf_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                iperf_output = result.stdout.decode()
                iperf_logs.append(iperf_output)
                logger.info(f"Executed iperf3 command: {iperf_command}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to execute iperf3 command: {e.stderr.decode()}")
                raise RuntimeError(f"Iperf3 command failed: {e.stderr.decode()}")

            logger.info(f"Sleeping for {interval:.2f} seconds...")
            time.sleep(interval)
            elapsed_time += interval
            if elapsed_time >= total_duration:
                break

        return jsonify({"message": "IPerf3 tests completed successfully."})

    except (ValueError, KeyError, AssertionError) as e:
        logger.error(f"Invalid input: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error running iperf3 tests: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/iperf_logs', methods=['GET'])
def get_iperf_logs():
    global iperf_logs
    formatted_logs = []

    for log_entry in iperf_logs:
        try:
            log_data = json.loads(log_entry)
            formatted_logs.append(log_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error processing iperf log: {str(e)}")

    iperf_logs = []  # Clear logs after retrieval
    return jsonify({"iperf_logs": formatted_logs})


if __name__ == '__main__':
    app.run(host='192.168.70.135', port=5001, debug=True)
