import os
import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 38083
_last_cpu_ticks = None

def get_stats():
    global _last_cpu_ticks
    try:
        temp = subprocess.check_output(["ubnt-systool", "cputemp"], text=True).strip()
    except Exception:
        temp = "Error"

    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = list(map(int, line.split()[1:5]))
        total = sum(parts)
        idle = parts[3]
        if _last_cpu_ticks is None:
            _last_cpu_ticks = [total, idle]
            cpu_util = 0
        else:
            diff_total = total - _last_cpu_ticks[0]
            diff_idle = idle - _last_cpu_ticks[1]
            _last_cpu_ticks = [total, idle]
            cpu_util = round((1.0 - (diff_idle / diff_total)) * 100, 1) if diff_total > 0 else 0
    except Exception:
        cpu_util = 0

    try:
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem_info[parts[0].replace(':', '')] = int(parts[1])
        total_mem = mem_info.get('MemTotal', 1)
        avail_mem = mem_info.get('MemAvailable', mem_info.get('MemFree', 0))
        mem_util = round(((total_mem - avail_mem) / total_mem) * 100, 1)
    except Exception:
        mem_util = 0

    return json.dumps({"temp": temp, "cpu": cpu_util, "mem": mem_util})

class TempServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(get_stats().encode())
            return

        # Serve the local copy of Chart.js directly from the console disk space
        if self.path == '/chart.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            try:
                with open('/root/ucg-dash/chart.js', 'rb') as f:
                    self.wfile.write(f.read())
            except Exception:
                self.send_error(404, "chart.js file missing")
            return

        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open('/root/ucg-dash/index.html', 'rb') as f:
                    self.wfile.write(f.read())
            except Exception:
                self.wfile.write(b"Error: index.html missing.")
            return

        self.send_error(404, "File Not Found")

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), TempServer)
    print(f"Server starting on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
