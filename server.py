import os
import time
import json
import threading
import subprocess
from datetime import datetime
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# FIX: Expanded buffer size to track exactly 24 hours of data history
MAX_BUFFER_SIZE = 8640
stats_buffer = deque(maxlen=MAX_BUFFER_SIZE)

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
                parts = line.split()
                if not parts:
                    continue
                timestamp_str = parts[0]
                if len(timestamp_str) > 22 and timestamp_str[-3] == ":":
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

class UCGDashHTTPHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Route 1: Real-time window data stream (returns everything up to total max buffer)
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(list(stats_buffer)).encode("utf-8"))
            return
            
        # ADDED Route 2: Server-side downsampling (slices history array every 5 minutes / 30 points)
        elif self.path == "/api/stats/24h":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            raw_list = list(stats_buffer)
            downsampled = raw_list[::30]  # Take every 30th entry (10s * 30 = 5 minutes)
            self.wfile.write(json.dumps(downsampled).encode("utf-8"))
            return
            
        elif self.path == "/" or self.path == "/index.html":
            self.serve_static_file(os.path.join(STATIC_DIR, 'index.html'), "text/html")
            return      
        elif self.path == "/static/favicon.ico":
            self.serve_static_file(os.path.join(STATIC_DIR, 'favicon.ico'), "image/x-icon")
            return
        elif self.path == "/static/chart.js":
            self.serve_static_file(os.path.join(STATIC_DIR, 'chart.js'), "application/javascript")
            return
        else:
            self.send_error(404, "File Not Found")

    def serve_static_file(self, file_path, content_type):
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, f"Missing Asset: {os.path.basename(file_path)}")
        except Exception as e:
            self.send_error(500, f"Error: {e}")

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    ticker = threading.Thread(target=background_metrics_logger, daemon=True)
    ticker.start()
    HTTPServer(('0.0.0.0', 5000), UCGDashHTTPHandler).serve_forever()
