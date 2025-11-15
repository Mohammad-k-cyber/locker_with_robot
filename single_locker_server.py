#!/usr/bin/env python3
"""
Single Locker Monitor - Simple Web Interface
Fetches data from main server at 72.61.181.1:8080
Displays one locker's status in real-time
"""

import requests
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ========== CONFIGURATION ==========

# Main server settings (where ESP32 is connected)
MAIN_SERVER_IP = "72.61.181.1"
MAIN_SERVER_PORT = 8080
SERVER_PASSWORD = "Cyber@Abed1102"

# This monitor's web interface
MONITOR_PORT = 9090  # Different port to avoid conflict

# Target locker to display
TARGET_LOCKER = 1  # Which locker to monitor (1-12)

# ===================================


class LockerDataFetcher:
    """Fetches locker data from main server"""
    
    def __init__(self):
        self.base_url = f"http://{MAIN_SERVER_IP}"
        self.session_cookie = None
        self.last_status = None
        self.is_connected = False
        
        # Login to main server
        self._login()
        
        # Start background update thread
        self.running = True
        threading.Thread(target=self._update_loop, daemon=True).start()
    
    def _login(self):
        """Login to main server"""
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json={"password": SERVER_PASSWORD},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.session_cookie = data.get('session')
                    self.is_connected = True
                    print(f"✅ Connected to main server: {self.base_url}")
                    return True
            
            print(f"❌ Login failed: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Cannot connect to main server: {e}")
            return False
    
    def _get_headers(self):
        """Get headers with session cookie"""
        return {
            "Cookie": f"session={self.session_cookie}",
            "Content-Type": "application/json"
        }
    
    def fetch_status(self):
        """Fetch current status from main server"""
        try:
            response = requests.get(
                f"{self.base_url}/api/status",
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                self.last_status = response.json()
                return self.last_status
            else:
                print(f"⚠️ Status fetch failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Error fetching status: {e}")
            self.is_connected = False
            return None
    
    def _update_loop(self):
        """Background thread to update status"""
        while self.running:
            self.fetch_status()
            time.sleep(1)  # Update every second
    
    def get_locker_data(self, locker_num):
        """Get data for specific locker"""
        if not self.last_status:
            return None
        
        lockers = self.last_status.get('lockers', {})
        return lockers.get(str(locker_num))
    
    def get_system_status(self):
        """Get overall system status"""
        if not self.last_status:
            return {
                'connected': False,
                'uptime': 0,
                'total_commands': 0
            }
        
        return {
            'connected': self.last_status.get('connected', False),
            'uptime': self.last_status.get('uptime', 0),
            'total_commands': self.last_status.get('total_commands', 0)
        }


# Global data fetcher
data_fetcher = LockerDataFetcher()


class MonitorHandler(BaseHTTPRequestHandler):
    """Simple web interface handler"""
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_monitor_page().encode())
        
        elif self.path == '/api/data':
            # API endpoint for locker data
            locker_data = data_fetcher.get_locker_data(TARGET_LOCKER)
            system_status = data_fetcher.get_system_status()
            
            response = {
                'locker_num': TARGET_LOCKER,
                'locker': locker_data,
                'system': system_status
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_monitor_page(self):
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Locker #{TARGET_LOCKER} Monitor</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 30px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .server-info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 0.9em;
            color: #666;
        }}
        .locker-display {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }}
        .locker-number {{
            font-size: 4em;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }}
        .status-item {{
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .status-item.changed {{
            animation: pulse 0.5s ease;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); background: rgba(255,255,255,0.3); }}
        }}
        .status-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        .status-value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .status-text {{
            font-size: 0.8em;
            margin-top: 10px;
        }}
        .system-status {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 0.85em;
            margin-top: 20px;
        }}
        .offline {{
            background: #dc3545 !important;
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Locker Monitor</h1>
        
        <div class="server-info">
            📡 Connected to: {MAIN_SERVER_IP}:{MAIN_SERVER_PORT}
        </div>
        
        <div id="offlineAlert" class="offline" style="display: none;">
            ⚠️ Cannot connect to main server
        </div>
        
        <div class="locker-display">
            <div class="locker-number">#{TARGET_LOCKER}</div>
            <div class="status-grid">
                <div class="status-item" id="doorStatusItem">
                    <div class="status-label">Door Status</div>
                    <div class="status-value" id="doorStatus">❓</div>
                    <div class="status-text" id="doorText">Unknown</div>
                </div>
                <div class="status-item" id="sensorStatusItem">
                    <div class="status-label">IR Sensor</div>
                    <div class="status-value" id="sensorStatus">❓</div>
                    <div class="status-text" id="sensorText">Unknown</div>
                </div>
            </div>
        </div>
        
        <div class="system-status">
            <div class="stat">
                <div class="stat-label">ESP32</div>
                <div class="stat-value" id="connection">⏳</div>
            </div>
            <div class="stat">
                <div class="stat-label">Commands</div>
                <div class="stat-value" id="commands">0</div>
            </div>
            <div class="stat">
                <div class="stat-label">Uptime</div>
                <div class="stat-value" id="uptime">0s</div>
            </div>
        </div>
        
        <div class="footer">
            Last update: <span id="lastUpdate">--:--:--</span>
        </div>
    </div>
    
    <script>
        let previousDoorOpen = null;
        let previousSensor = null;
        
        async function updateData() {{
            try {{
                const res = await fetch('/api/data');
                const data = await res.json();
                
                // Hide offline alert
                document.getElementById('offlineAlert').style.display = 'none';
                
                // Update system status
                const system = data.system;
                document.getElementById('connection').textContent = system.connected ? '🟢' : '🔴';
                document.getElementById('commands').textContent = system.total_commands;
                document.getElementById('uptime').textContent = system.uptime + 's';
                
                // Update locker status
                const locker = data.locker;
                
                if (locker) {{
                    // Door status
                    const doorEl = document.getElementById('doorStatus');
                    const doorTextEl = document.getElementById('doorText');
                    const doorItem = document.getElementById('doorStatusItem');
                    
                    if (locker.door_open !== previousDoorOpen && previousDoorOpen !== null) {{
                        doorItem.classList.add('changed');
                        setTimeout(() => doorItem.classList.remove('changed'), 500);
                    }}
                    previousDoorOpen = locker.door_open;
                    
                    if (locker.door_open) {{
                        doorEl.textContent = '🔓';
                        doorTextEl.textContent = 'OPEN';
                        doorItem.style.background = 'rgba(40, 167, 69, 0.3)';
                    }} else {{
                        doorEl.textContent = '🔒';
                        doorTextEl.textContent = 'CLOSED';
                        doorItem.style.background = 'rgba(255, 255, 255, 0.2)';
                    }}
                    
                    // Sensor status
                    const sensorEl = document.getElementById('sensorStatus');
                    const sensorTextEl = document.getElementById('sensorText');
                    const sensorItem = document.getElementById('sensorStatusItem');
                    
                    if (locker.sensor_status !== previousSensor && previousSensor !== null) {{
                        sensorItem.classList.add('changed');
                        setTimeout(() => sensorItem.classList.remove('changed'), 500);
                    }}
                    previousSensor = locker.sensor_status;
                    
                    if (locker.sensor_status === 'Empty') {{
                        sensorEl.textContent = '✅';
                        sensorTextEl.textContent = 'Empty';
                    }} else if (locker.sensor_status === 'Occupied') {{
                        sensorEl.textContent = '📦';
                        sensorTextEl.textContent = 'Occupied';
                    }} else {{
                        sensorEl.textContent = '❓';
                        sensorTextEl.textContent = 'Unknown';
                    }}
                }} else {{
                    // No data available
                    document.getElementById('doorStatus').textContent = '❌';
                    document.getElementById('doorText').textContent = 'No Data';
                    document.getElementById('sensorStatus').textContent = '❌';
                    document.getElementById('sensorText').textContent = 'No Data';
                }}
                
                // Update timestamp
                const now = new Date();
                document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
                
            }} catch(e) {{
                console.error('Update error:', e);
                document.getElementById('offlineAlert').style.display = 'block';
            }}
        }}
        
        // Update every second
        setInterval(updateData, 1000);
        
        // Initial update
        updateData();
        
        console.log('Monitor initialized - updating every 1 second');
    </script>
</body>
</html>"""


def main():
    print("=" * 60)
    print(f"🔐 Single Locker Monitor - Locker #{TARGET_LOCKER}")
    print("=" * 60)
    print(f"Main Server: {MAIN_SERVER_IP}:{MAIN_SERVER_PORT}")
    print(f"Monitor Port: {MONITOR_PORT}")
    print("=" * 60)
    
    # Give data fetcher a moment to connect
    time.sleep(1)
    
    # Start web server
    server = HTTPServer(('0.0.0.0', MONITOR_PORT), MonitorHandler)
    
    print(f"\n🌐 Monitor Interface: http://localhost:{MONITOR_PORT}")
    print(f"🎯 Monitoring Locker: #{TARGET_LOCKER}")
    print("\n✅ System running. Press Ctrl+C to stop.")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped")
        data_fetcher.running = False


if __name__ == "__main__":
    main()