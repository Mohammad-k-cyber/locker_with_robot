#!/usr/bin/env python3
"""
Main Controller - Locker & Robot Integration with Cycle Management
Strict Logic:
1. Check locker is CLOSED (initial state)
2. Open locker
3. Verify locker changed from CLOSED to OPEN directly
4. Execute robot sequence
5. Verify locker changed from OPEN back to CLOSED
6. Repeat
"""

import requests
import json
import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from locker_client import LockerClient
from robot_controller import SimpleRobotController

# ========== CONFIGURATION ==========

MAIN_SERVER_IP = "72.61.181.1"
MAIN_SERVER_PORT = 8080
MONITOR_PORT = 9091
TARGET_LOCKER = 1
ROBOT_IP = "192.168.58.101"

LOCKER_OPEN_TIMEOUT = 10
LOCKER_CLOSE_TIMEOUT = 30
MAX_OPEN_RETRIES = 3
RETRY_DELAY = 2
LOG_FILE = "cycle_controller.log"

# ===================================


class CycleController:
    """Main controller managing the complete cycle workflow"""
    
    def __init__(self):
        """Initialize the cycle controller"""
        # Setup file logging (for detailed logs)
        self.file_logger = logging.getLogger("FileLogger")
        file_handler = logging.FileHandler(LOG_FILE)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.file_logger.addHandler(file_handler)
        self.file_logger.setLevel(logging.DEBUG)
        
        # Setup console logging (minimal)
        self.console_logger = logging.getLogger("ConsoleLogger")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self.console_logger.addHandler(console_handler)
        self.console_logger.setLevel(logging.INFO)
        
        self.file_logger.info("="*80)
        self.file_logger.info("CYCLE CONTROLLER STARTED")
        self.file_logger.info("="*80)
        
        # Cycle tracking
        self.cycle_count = 0
        self.cycle_history = []
        self.current_cycle_status = {
            'cycle_num': 0,
            'phase': 'Initializing',
            'locker_status': 'Unknown',
            'robot_status': 'Unknown',
            'status': 'Idle',
            'timestamp': None,
            'error': None,
            'duration': 0
        }
        
        # Statistics tracking
        self.successful_cycles = 0
        self.failed_cycles = 0
        self.start_time = time.time()
        
        # System status
        self.system_running = True
        self.server_connected = False
        self.robot_connected = False
        
        # Client instances
        self.locker_client = None
        self.robot_controller = None
        
        # Initialize clients
        self._initialize_clients()
        
        # Start cycle loop in background thread
        self.running = True
        self.cycle_thread = threading.Thread(target=self._cycle_loop, daemon=True)
        self.cycle_thread.start()
        
        self.file_logger.info("✅ Cycle Controller initialized")
        self._print_console_status()
    
    def _initialize_clients(self):
        """Initialize locker client and robot controller"""
        self.file_logger.info("Initializing clients...")
        
        try:
            self.file_logger.info("Connecting to locker server...")
            self.locker_client = LockerClient(
                server_ip=MAIN_SERVER_IP,
                port=MAIN_SERVER_PORT
            )
            self.server_connected = True
            self.file_logger.info("✅ Locker client connected")
            
        except Exception as e:
            self.file_logger.error(f"❌ Failed to connect locker client: {e}")
            self.server_connected = False
        
        try:
            self.file_logger.info("Connecting to robot...")
            self.robot_controller = SimpleRobotController(robot_ip=ROBOT_IP)
            self.robot_connected = True
            self.file_logger.info("✅ Robot controller connected")
            
        except Exception as e:
            self.file_logger.error(f"❌ Failed to connect robot controller: {e}")
            self.robot_connected = False
    
    def _print_console_status(self):
        """Print minimal status to console"""
        server_status = "🟢 Connected" if self.server_connected else "🔴 Disconnected"
        robot_status = "🟢 Connected" if self.robot_connected else "🔴 Disconnected"
        self.console_logger.info(f"Server: {server_status} | Robot: {robot_status}")
    
    def _cycle_loop(self):
        """Main cycle execution loop (runs in background thread)"""
        self.file_logger.info("🔄 Starting cycle loop")
        
        while self.running:
            if self.server_connected and self.robot_connected:
                self.cycle_count += 1
                self._execute_cycle()
            else:
                self.file_logger.warning("⚠️ Not all systems connected, retrying connection...")
                self._reinitialize_if_needed()
                time.sleep(5)
    
    def _reinitialize_if_needed(self):
        """Try to reconnect if systems are disconnected"""
        if not self.server_connected or not self.robot_connected:
            self.file_logger.info("Attempting to reconnect to systems...")
            self._initialize_clients()
            self._print_console_status()
    
    def _execute_cycle(self):
        """Execute one complete cycle"""
        cycle_start = time.time()
        start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.current_cycle_status = {
            'cycle_num': self.cycle_count,
            'phase': 'Starting',
            'locker_status': 'Unknown',
            'robot_status': 'Unknown',
            'status': 'In Progress',
            'timestamp': datetime.now().isoformat(),
            'error': None,
            'duration': 0
        }
        
        self.console_logger.info(f"[{start_time_str}] CYCLE #{self.cycle_count} STARTED")
        self.file_logger.info(f"\n{'='*80}")
        self.file_logger.info(f"CYCLE #{self.cycle_count} - STARTED at {start_time_str}")
        self.file_logger.info(f"{'='*80}")
        
        try:
            # ============== PHASE 0: Check Initial Locker State ==============
            self.current_cycle_status['phase'] = 'Checking Initial State'
            self.file_logger.info("[Phase 0] Checking initial locker state (must be CLOSED)...")
            
            initial_status = self._get_locker_status()
            if initial_status != "Closed":
                raise Exception(f"❌ Locker is not in CLOSED state (current: {initial_status}). Cannot start cycle.")
            
            self.file_logger.info("✅ Locker confirmed CLOSED - Ready to start cycle")
            
            # ============== PHASE 1: Check Connection ==============
            self.current_cycle_status['phase'] = 'Checking Connection'
            self.file_logger.info("[Phase 1] Checking server connection...")
            
            if not self._check_server_connection():
                raise Exception("❌ Server connection failed")
            
            self.file_logger.info("✅ Server connection OK")
            
            # ============== PHASE 2: Open Locker ==============
            self.current_cycle_status['phase'] = 'Opening Locker'
            self.file_logger.info("[Phase 2] Opening locker...")
            
            if not self._open_locker_with_retry():
                raise Exception("❌ Failed to open locker after retries")
            
            # ============== PHASE 3: Verify State Change (CLOSED → OPEN) ==============
            self.current_cycle_status['phase'] = 'Verifying State Change'
            self.file_logger.info("[Phase 3] Verifying locker changed from CLOSED to OPEN...")
            
            if not self._verify_locker_open():
                raise Exception("❌ Locker status did not change to OPEN")
            
            self.current_cycle_status['locker_status'] = 'OPEN'
            self.file_logger.info("✅ Locker status confirmed: CLOSED → OPEN (state change verified)")
            
            # ============== PHASE 4: Execute Robot Sequence ==============
            self.current_cycle_status['phase'] = 'Robot Sequence'
            self.file_logger.info("[Phase 4] Executing robot motion sequence (locker is OPEN)...")
            
            if not self._execute_robot_sequence():
                raise Exception("❌ Robot sequence execution failed")
            
            self.current_cycle_status['robot_status'] = 'COMPLETED'
            self.file_logger.info("✅ Robot sequence completed - returned to home position")
            
            # ============== PHASE 5: Verify State Change (OPEN → CLOSED) ==============
            self.current_cycle_status['phase'] = 'Verifying Close State'
            self.file_logger.info("[Phase 5] Verifying locker changed from OPEN back to CLOSED...")
            
            if not self._verify_locker_closed():
                raise Exception("❌ CRITICAL: Locker did not close! Aborting cycle. Physical inspection required.")
            
            self.current_cycle_status['locker_status'] = 'CLOSED'
            self.file_logger.info("✅ Locker status confirmed: OPEN → CLOSED (state change verified)")
            
            # ============== Cycle Complete ==============
            self.current_cycle_status['phase'] = 'Complete'
            self.current_cycle_status['status'] = 'Success'
            self.current_cycle_status['error'] = None
            
            cycle_duration = time.time() - cycle_start
            self.current_cycle_status['duration'] = cycle_duration
            
            # Increment success counter
            self.successful_cycles += 1
            
            self.console_logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CYCLE #{self.cycle_count} COMPLETED in {cycle_duration:.2f}s ✅")
            self.file_logger.info(f"✅ CYCLE #{self.cycle_count} COMPLETED in {cycle_duration:.2f}s")
            self.file_logger.info(f"   State changes: CLOSED → OPEN → CLOSED (verified)")
            self.file_logger.info(f"   📊 Statistics: {self.successful_cycles} Success | {self.failed_cycles} Failed")
            self.file_logger.info(f"{'='*80}\n")
            
            # Store in history
            self.cycle_history.append(self.current_cycle_status.copy())
            
            # Keep only last 50 cycles in history
            if len(self.cycle_history) > 50:
                self.cycle_history = self.cycle_history[-50:]
        
        except Exception as e:
            self.file_logger.error(f"❌ Cycle Error: {str(e)}")
            
            cycle_duration = time.time() - cycle_start
            self.current_cycle_status['duration'] = cycle_duration
            self.current_cycle_status['status'] = 'Failed'
            self.current_cycle_status['error'] = str(e)
            self.current_cycle_status['phase'] = 'Error'
            
            # Increment failure counter
            self.failed_cycles += 1
            
            self.console_logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CYCLE #{self.cycle_count} FAILED ❌")
            self.file_logger.info(f"   Error: {str(e)}")
            self.file_logger.info(f"   📊 Statistics: {self.successful_cycles} Success | {self.failed_cycles} Failed")
            self.file_logger.info(f"{'='*80}\n")
            
            # Store in history
            self.cycle_history.append(self.current_cycle_status.copy())
            if len(self.cycle_history) > 50:
                self.cycle_history = self.cycle_history[-50:]
    
    def _get_locker_status(self):
        """Get current locker status"""
        try:
            status = self.locker_client.lockerStatus(TARGET_LOCKER)
            return status  # Returns: "Open", "Closed", or "Unknown"
        except Exception as e:
            self.file_logger.error(f"Error getting locker status: {e}")
            return "Unknown"
    
    def _check_server_connection(self):
        """Check if server is connected and responsive"""
        try:
            status = self.locker_client.get_status()
            if status:
                return True
            return False
        except Exception as e:
            self.file_logger.error(f"Connection check failed: {e}")
            return False
    
    def _open_locker_with_retry(self):
        """Open locker with retry mechanism"""
        for attempt in range(1, MAX_OPEN_RETRIES + 1):
            try:
                self.file_logger.info(f"  Attempt {attempt}/{MAX_OPEN_RETRIES}: Sending open command to locker {TARGET_LOCKER}...")
                
                result = self.locker_client.openLocker(TARGET_LOCKER)
                
                if result:
                    self.file_logger.info(f"  ✅ Open command sent successfully")
                    return True
                else:
                    self.file_logger.warning(f"  ⚠️ Attempt {attempt} failed")
                    if attempt < MAX_OPEN_RETRIES:
                        self.file_logger.info(f"     Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        
            except Exception as e:
                self.file_logger.error(f"  ❌ Attempt {attempt} error: {e}")
                if attempt < MAX_OPEN_RETRIES:
                    time.sleep(RETRY_DELAY)
        
        return False
    
    def _verify_locker_open(self):
        """Verify locker changed from CLOSED to OPEN"""
        start_time = time.time()
        self.file_logger.info(f"  Waiting for state change: CLOSED → OPEN (timeout: {LOCKER_OPEN_TIMEOUT}s)...")
        
        while (time.time() - start_time) < LOCKER_OPEN_TIMEOUT:
            try:
                status = self._get_locker_status()
                
                if status == "Open":
                    elapsed = time.time() - start_time
                    self.file_logger.info(f"  ✅ State change verified: CLOSED → OPEN (confirmed after {elapsed:.1f}s)")
                    return True
                elif status == "Closed":
                    self.file_logger.debug(f"  ⏳ Still CLOSED, waiting...")
                else:
                    self.file_logger.debug(f"  ⏳ Status: {status}")
                
                time.sleep(0.5)
                
            except Exception as e:
                self.file_logger.error(f"  Error checking locker status: {e}")
                time.sleep(0.5)
        
        self.file_logger.error(f"  ❌ State change NOT detected within {LOCKER_OPEN_TIMEOUT}s")
        return False
    
    def _execute_robot_sequence(self):
        """Execute robot motion sequence (only when locker is OPEN)"""
        try:
            # Verify locker is still OPEN before executing
            current_status = self._get_locker_status()
            if current_status != "Open":
                self.file_logger.error(f"  ❌ SAFETY CHECK FAILED: Locker is not OPEN (current: {current_status})")
                return False
            
            self.file_logger.info("  ✅ Safety check: Locker is OPEN - Proceeding with robot sequence")
            self.file_logger.info("  Starting robot sequence: home → position_1 → home")
            
            success = self.robot_controller.execute_motion_sequence()
            
            if success:
                self.file_logger.info("  ✅ Robot sequence completed - returned to home")
            return success
            
        except Exception as e:
            self.file_logger.error(f"Robot execution error: {e}")
            return False
    
    def _verify_locker_closed(self):
        """Verify locker changed from OPEN to CLOSED (NO RETRIES - STRICT)"""
        start_time = time.time()
        self.file_logger.info(f"  Waiting for state change: OPEN → CLOSED (timeout: {LOCKER_CLOSE_TIMEOUT}s)...")
        
        while (time.time() - start_time) < LOCKER_CLOSE_TIMEOUT:
            try:
                status = self._get_locker_status()
                
                if status == "Closed":
                    elapsed = time.time() - start_time
                    self.file_logger.info(f"  ✅ State change verified: OPEN → CLOSED (confirmed after {elapsed:.1f}s)")
                    return True
                elif status == "Open":
                    self.file_logger.debug(f"  ⏳ Still OPEN, waiting for close...")
                else:
                    self.file_logger.debug(f"  ⏳ Status: {status}")
                
                time.sleep(0.5)
                
            except Exception as e:
                self.file_logger.error(f"  Error checking locker status: {e}")
                time.sleep(0.5)
        
        # STRICT: No retry - if locker doesn't close, FAIL and require intervention
        self.file_logger.error(f"  ❌ CRITICAL: Locker DID NOT CLOSE within {LOCKER_CLOSE_TIMEOUT}s")
        self.file_logger.error(f"  ❌ This cycle FAILED - NO RETRIES - PHYSICAL INSPECTION REQUIRED")
        return False
    
    def get_status(self):
        """Get current system status"""
        return {
            'running': self.running,
            'cycle_count': self.cycle_count,
            'successful_cycles': self.successful_cycles,
            'failed_cycles': self.failed_cycles,
            'server_connected': self.server_connected,
            'robot_connected': self.robot_connected,
            'current_cycle': self.current_cycle_status,
            'recent_cycles': self.cycle_history[-10:] if self.cycle_history else []
        }
    
    def print_final_statistics(self):
        """Print final statistics summary"""
        total_runtime = time.time() - self.start_time
        runtime_hours = int(total_runtime // 3600)
        runtime_minutes = int((total_runtime % 3600) // 60)
        runtime_seconds = int(total_runtime % 60)
        
        total_cycles = self.successful_cycles + self.failed_cycles
        success_rate = (self.successful_cycles / total_cycles * 100) if total_cycles > 0 else 0
        
        summary = f"""
{'='*80}
                    FINAL STATISTICS SUMMARY
{'='*80}
Total Runtime:        {runtime_hours:02d}:{runtime_minutes:02d}:{runtime_seconds:02d} (HH:MM:SS)
Total Cycles:         {total_cycles}
✅ Successful Cycles: {self.successful_cycles}
❌ Failed Cycles:     {self.failed_cycles}
Success Rate:         {success_rate:.1f}%
{'='*80}
"""
        
        # Print to both console and file
        self.console_logger.info(summary)
        self.file_logger.info(summary)
        
        return summary


controller = None


class MonitorHandler(BaseHTTPRequestHandler):
    """Web interface handler"""
    
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_monitor_page().encode())
        
        elif self.path == '/api/status':
            status = controller.get_status()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_monitor_page(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Locker-Robot Cycle Controller</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .status-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .status-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        .cycle-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        }
        .cycle-number {
            font-size: 3.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .cycle-number-label {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .stats-bar {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .stat-box {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .phase-display {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        .phase-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        .phase-text {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
        }
        .history-container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .history-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 20px;
        }
        .history-item {
            display: grid;
            grid-template-columns: 80px 1fr 100px auto;
            gap: 15px;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
        }
        .history-item:last-child {
            border-bottom: none;
        }
        .cycle-num {
            font-weight: bold;
            color: #667eea;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
        .failed {
            color: #dc3545;
            font-weight: bold;
        }
        .duration {
            color: #999;
            text-align: right;
        }
        .connection-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }
        .connected {
            background: #d4edda;
            color: #155724;
        }
        .disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        .error-display {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .error-display.show {
            display: block;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .running {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Locker-Robot Cycle Controller</h1>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">🔌 System Status</div>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-label">Server</div>
                        <div class="status-value" id="serverStatus">⏳</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Robot</div>
                        <div class="status-value" id="robotStatus">⏳</div>
                    </div>
                </div>
                <div style="margin-top: 15px; font-size: 0.9em;">
                    <div id="connectionBadges"></div>
                </div>
            </div>
        </div>
        
        <div class="cycle-info">
            <div class="cycle-number-label">CYCLE COUNT</div>
            <div class="cycle-number" id="cycleCount">0</div>
            <div class="stats-bar">
                <div class="stat-box">
                    <div class="stat-label">✅ Successful</div>
                    <div class="stat-number" id="successCount">0</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">❌ Failed</div>
                    <div class="stat-number" id="failedCount">0</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">📊 Current Cycle Status</div>
            
            <div class="error-display" id="errorDisplay"></div>
            
            <div class="phase-display">
                <div class="phase-label">Current Phase</div>
                <div class="phase-text" id="currentPhase">Initializing</div>
            </div>
            
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">Locker Status</div>
                    <div class="status-value" id="lockerStatus">❓</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Robot Status</div>
                    <div class="status-value" id="robotMotorStatus">❓</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Cycle Status</div>
                    <div class="status-value" id="cycleStatus">⏳</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Duration</div>
                    <div class="status-value" id="cycleDuration" style="font-size: 1.2em;">0s</div>
                </div>
            </div>
        </div>
        
        <div class="history-container" style="margin-top: 30px;">
            <div class="history-title">📋 Cycle History (Last 10)</div>
            <div id="historyList" style="max-height: 400px; overflow-y: auto;"></div>
        </div>
    </div>
    
    <script>
        async function updateStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                const serverConnected = data.server_connected;
                const robotConnected = data.robot_connected;
                
                document.getElementById('serverStatus').textContent = serverConnected ? '🟢' : '🔴';
                document.getElementById('robotStatus').textContent = robotConnected ? '🟢' : '🔴';
                
                let badges = '';
                badges += `<span class="connection-badge ${serverConnected ? 'connected' : 'disconnected'}">
                    ${serverConnected ? '✅' : '❌'} Server
                </span>`;
                badges += `<span class="connection-badge ${robotConnected ? 'connected' : 'disconnected'}">
                    ${robotConnected ? '✅' : '❌'} Robot
                </span>`;
                document.getElementById('connectionBadges').innerHTML = badges;
                
                document.getElementById('cycleCount').textContent = data.cycle_count;
                document.getElementById('successCount').textContent = data.successful_cycles || 0;
                document.getElementById('failedCount').textContent = data.failed_cycles || 0;
                
                const cycle = data.current_cycle;
                document.getElementById('currentPhase').textContent = cycle.phase || 'Idle';
                
                const phaseEl = document.querySelector('.phase-text');
                if (cycle.status === 'In Progress') {
                    phaseEl.parentElement.classList.add('running');
                } else {
                    phaseEl.parentElement.classList.remove('running');
                }
                
                const lockerStatusEl = document.getElementById('lockerStatus');
                if (cycle.locker_status === 'OPEN') {
                    lockerStatusEl.textContent = '🔓';
                } else if (cycle.locker_status === 'CLOSED') {
                    lockerStatusEl.textContent = '🔒';
                } else {
                    lockerStatusEl.textContent = '❓';
                }
                
                const robotMotorStatusEl = document.getElementById('robotMotorStatus');
                if (cycle.robot_status === 'COMPLETED') {
                    robotMotorStatusEl.textContent = '✅';
                } else if (cycle.robot_status === 'In Progress') {
                    robotMotorStatusEl.textContent = '⚙️';
                } else {
                    robotMotorStatusEl.textContent = '⏳';
                }
                
                const cycleStatusEl = document.getElementById('cycleStatus');
                if (cycle.status === 'Success') {
                    cycleStatusEl.textContent = '✅';
                    cycleStatusEl.style.color = '#28a745';
                } else if (cycle.status === 'Failed') {
                    cycleStatusEl.textContent = '❌';
                    cycleStatusEl.style.color = '#dc3545';
                } else if (cycle.status === 'In Progress') {
                    cycleStatusEl.textContent = '⏳';
                    cycleStatusEl.style.color = '#ffc107';
                } else {
                    cycleStatusEl.textContent = '⏸';
                    cycleStatusEl.style.color = '#999';
                }
                
                document.getElementById('cycleDuration').textContent = cycle.duration.toFixed(1) + 's';
                
                const errorDisplay = document.getElementById('errorDisplay');
                if (cycle.error) {
                    errorDisplay.textContent = '⚠️ ' + cycle.error;
                    errorDisplay.classList.add('show');
                } else {
                    errorDisplay.classList.remove('show');
                }
                
                const historyList = document.getElementById('historyList');
                historyList.innerHTML = '';
                
                const recentCycles = data.recent_cycles || [];
                recentCycles.reverse().forEach(c => {
                    const statusClass = c.status === 'Success' ? 'success' : 'failed';
                    const statusEmoji = c.status === 'Success' ? '✅' : '❌';
                    
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    item.innerHTML = `
                        <div class="cycle-num">#${c.cycle_num}</div>
                        <div>${c.phase}</div>
                        <div class="${statusClass}">${statusEmoji} ${c.status}</div>
                        <div class="duration">${c.duration.toFixed(1)}s</div>
                    `;
                    historyList.appendChild(item);
                });
                
            } catch(e) {
                console.error('Update error:', e);
            }
        }
        
        setInterval(updateStatus, 1000);
        updateStatus();
        
        console.log('Cycle Monitor initialized');
    </script>
</body>
</html>"""


def main():
    """Main entry point"""
    global controller
    
    print("=" * 60)
    print("🤖 LOCKER-ROBOT CYCLE CONTROLLER")
    print("=" * 60)
    print(f"Server: {MAIN_SERVER_IP}:{MAIN_SERVER_PORT}")
    print(f"Robot: {ROBOT_IP}")
    print(f"Target Locker: #{TARGET_LOCKER}")
    print(f"Web Interface: http://localhost:{MONITOR_PORT}")
    print(f"Detailed Logs: {LOG_FILE}")
    print("=" * 60)
    
    controller = CycleController()
    
    time.sleep(2)
    
    server = HTTPServer(('0.0.0.0', MONITOR_PORT), MonitorHandler)
    
    print(f"\n✅ System ready!")
    print(f"🌐 Open browser: http://localhost:{MONITOR_PORT}")
    print("📊 Monitor cycles in real-time")
    print("\n🛑 Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down controller...")
        controller.running = False
        
        # Print final statistics
        controller.print_final_statistics()
        
        print("\n✅ Controller stopped gracefully")
        print("=" * 60)


if __name__ == "__main__":
    main()