import os
import time
import threading
import subprocess
from datetime import datetime
from collections import deque
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import psutil

# Dynamically locate the directory where server.py is currently installed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR)
CORS(app)

MAX_BUFFER_SIZE = 100
stats_buffer = deque(maxlen=MAX_BUFFER_SIZE)

# Threat tracking states
threat_timestamps = []
last_file_position = 0
LOG_FILE_PATH = "/var/log/ulog/threat.log"

def process_new_threat_lines():
    global last_file_position, threat_timestamps
    if not os.path.exists(LOG_FILE_PATH):
        return
    try:
        current_size = os.path.getsize(LOG_FILE_PATH)
        if current_size < last_file_position:
            last_file_position = 0

        with open(LOG_FILE_PATH, "r") as f:
            f.seek(last_file_position)
            lines = f.readlines()
            last_file_position = f.tell()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                # Format match: '2026-08-10T12:35:47-07:00'
                timestamp_str = line.split()[0]
                
                # Dynamic fix for colon formatting in ISO-8601 offset strings
                if timestamp_str[-3] == ":":
                    timestamp_str = timestamp_str[:-3] + timestamp_str[-2:]
                
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
                threat_timestamps.append(dt.timestamp())
            except (ValueError, IndexError):
                continue
    except Exception as e:
        print(f"Error reading threat log stream: {e}")

def calculate_rolling_rates():
    global threat_timestamps
    now = time.time()
    threat_timestamps = [t for t in threat_timestamps if now - t <= 86400]
    threats_last_hour = sum(1 for t in threat_timestamps if now - t <= 3600)
    threats_last_day = len(threat_timestamps)
    return threats_last_hour, threats_last_day

def get_ubnt_cpu_load():
    try:
        output = subprocess.check_output(["ubnt-systool", "cpuload"], text=True)
        return float(output.strip())
    except (subprocess.SubprocessError, ValueError):
        return psutil.cpu_percent(interval=None)

def get_ubnt_temperature():
    try:
        output = subprocess.check_output(["ubnt-systool", "cputemp"], text=True)
        return float(output.strip())
    except (subprocess.SubprocessError, ValueError):
        return 0.0

def background_metrics_logger():
    global last_file_position
    if os.path.exists(LOG_FILE_PATH):
        last_file_position = os.path.getsize(LOG_FILE_PATH)

    while True:
        try:
            process_new_threat_lines()
            threats_p_hr, threats_p_day = calculate_rolling_rates()
            
            data_point = {
                "timestamp": int(time.time()),
                "cpu_load": get_ubnt_cpu_load(),
                "memory_used_pct": psutil.virtual_memory().percent,
                "temperature_c": get_ubnt_temperature(),
                "threat_rate_hour": threats_p_hr,
                "threat_rate_day": threats_p_day
            }
            stats_buffer.append(data_point)
        except Exception as e:
            print(f"Error gathering metrics: {e}")
        time.sleep(10)

# Serve the dashboard main view
@app.route("/", methods=["GET"])
def serve_dashboard():
    return send_from_directory(app.static_folder, 'index.html')

# Serve the asset relative to wherever the application directory lives
@app.route('/chart.js', methods=['GET'])
def serve_chart_js():
    return send_from_directory(app.static_folder, 'chart.js')

# Serve historical data points
@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(list(stats_buffer))

if __name__ == "__main__":
    ticker = threading.Thread(target=background_metrics_logger, daemon=True)
    ticker.start()
    app.run(host="0.0.0.0", port=5000)
