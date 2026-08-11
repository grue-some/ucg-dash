import os
import time
import json
import threading
import subprocess
from datetime import datetime
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
import psutil

# Dynamically locate the directory where server.py is currently installed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

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
                # Target format: '2026-08-10T12:35:47-07:00'
                parts = line.split()
                if not parts:
                    continue
                timestamp_str = parts[0]
                
                # Correct timezone colon mapping if required for older Python builds
                if len(timestamp_str) > 6 and timestamp_str[-3] == ":":
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
    """Custom native request handler routing API payloads and static files."""
    
    def end_headers(self):
        # Native CORS Header injections
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Respond to preflight CORS checks smoothly."""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Route 1: Telemetry dynamic API data endpoint
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            response_data = json.dumps(list(stats_buffer)).encode("utf-8")
            self.wfile.write(response_data)
            return

        # Route 2: Base UI Dashboard index route
        elif self.path == "/" or self.path == "/index.html":
            target_file = os.path.join(STATIC_DIR, 'index.html')
            self.serve_static_file(target_file, "text/html")
            return

        # Route 3: Local Chart JS relative script asset asset
        elif self.path == "/static/chart.js":
            target_file = os.path.join(STATIC_DIR, 'chart.js')
            self.serve_static_file(target_file, "application/javascript")
            return

        # Route 4: Fallback Handle for unmatched items
        else:
            self.send_error(404, "File Not Found")

    def serve_static_file(self, file_path, content_type):
        """Helper handler to securely read and serve local disk dependencies."""
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
            self.send_error(500, f"Internal Server Error: {e}")

    def log_message(self, format, *args):
        """Silences standard connection request prints to keep journalctl logs clean."""
        pass


if __name__ == "__main__":
    # Launch backend hardware metrics background loop thread
    ticker = threading.Thread(target=background_metrics_logger, daemon=True)
    ticker.start()
    
    # Establish local network HTTP server bindings
    server_address = ('0.0.0.0', 5000)
    httpd = HTTPServer(server_address, UCGDashHTTPHandler)
    print(f"UCG-Dash successfully running natively on http://localhost:5000")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()
