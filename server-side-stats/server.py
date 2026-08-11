import os
import time
import threading
import subprocess
from datetime import datetime
from collections import deque
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import psutil


# get location of chart.js and index.html
file_path_chart = os.path.join(os.getcwd(), "chart.js")
<! -- file_path_index = os.path.join(os.getcwd(), "index.html")
-->
# Configure Flask to know where your static assets live
app = Flask(__name__, static_folder=file_path_chart)
CORS(app)


# ... Keep all your existing buffer arrays and telemetry scraping methods exactly the same ...

MAX_BUFFER_SIZE = 100
stats_buffer = deque(maxlen=MAX_BUFFER_SIZE)

# Global tracker for log file position and threat history
threat_timestamps = []
last_file_position = 0
LOG_FILE_PATH = "/var/log/ulog/threat.log"

def process_new_threat_lines():
    """Reads only new lines from the log and extracts event timestamps."""
    global last_file_position, threat_timestamps
    
    if not os.path.exists(LOG_FILE_PATH):
        return

    try:
        # Check if file was rotated (size smaller than our last saved position)
        current_size = os.path.getsize(LOG_FILE_PATH)
        if current_size < last_file_position:
            last_file_position = 0  # Reset offset to read from beginning

        with open(LOG_FILE_PATH, "r") as f:
            f.seek(last_file_position)
            lines = f.readlines()
            last_file_position = f.tell()  # Save current position for next loop

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                # Format: '2026-08-10T12:35:47-07:00' -> Split by space to get timestamp token
                # Assumes the timestamp is the first word on the line
                timestamp_str = line.split()[0]
                
                # Handle the colon in the timezone offset for older Python versions if needed, 
                # but standard string splicing handles '%Y-%m-%dT%H:%M:%S%z' cleanly.
                # Strip out colons in timezone offset if necessary (e.g. -07:00 -> -0700)
                if timestamp_str[-3] == ":":
                    timestamp_str = timestamp_str[:-3] + timestamp_str[-2:]
                
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
                epoch_time = dt.timestamp()
                threat_timestamps.append(epoch_time)
            except (ValueError, IndexError) as e:
                # Skip malformed lines or lines without dates safely
                continue

    except Exception as e:
        print(f"Error reading log stream: {e}")

def calculate_rolling_rates():
    """Trims stale timestamps and extracts current window sliding counts."""
    global threat_timestamps
    now = time.time()
    
    # Prune elements older than 24 hours to keep memory thin
    threat_timestamps = [t for t in threat_timestamps if now - t <= 86400]
    
    # Calculate differential rates
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
    """Main execution loop tracking telemetry snapshots."""
    # Seed the initial file position to end-of-file on startup to avoid
    # parsing massive backlogs, or set to 0 to read historically on boot.
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


@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(list(stats_buffer))

# Add Route to serve the local dashboard asset directly from the gateway
@app.route('/static/chart.js', methods=['GET'])
def serve_chart_js():
    return send_from_directory(file_path_chart, 'chart.js')

if __name__ == "__main__":
    ticker = threading.Thread(target=background_metrics_logger, daemon=True)
    ticker.start()
    app.run(host="0.0.0.0", port=5000)
    
