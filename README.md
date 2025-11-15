# 🤖 Locker-Robot Integration System - Complete Documentation

**Version:** 2.0  
**Last Updated:** November 2025

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [System Architecture](#system-architecture)
3. [Hardware Components](#hardware-components)
4. [Software Components](#software-components)
5. [Installation & Setup](#installation--setup)
6. [Configuration Guide](#configuration-guide)
7. [Usage Guide](#usage-guide)
8. [API Reference](#api-reference)
9. [Cycle Flow & Logic](#cycle-flow--logic)
10. [Web Monitoring Interface](#web-monitoring-interface)
11. [Safety Features](#safety-features)
12. [Troubleshooting](#troubleshooting)
13. [Code Examples](#code-examples)
14. [Performance & Statistics](#performance--statistics)
15. [Advanced Topics](#advanced-topics)

---

## 🎯 System Overview

### What is this system?

This is an **automated locker-robot integration system** that coordinates the operation of smart lockers with a robotic arm. The system executes controlled cycles where:
1. A locker door is opened remotely
2. The door state is verified
3. A robot performs a predefined motion sequence
4. The locker door closure is verified
5. The cycle repeats continuously

### Key Features

✅ **Automated Cycle Management** - Continuous operation with strict state verification  
✅ **Real-time Monitoring** - Web-based dashboard for live system status  
✅ **Safety First** - Multiple verification steps and safety checks  
✅ **Statistics Tracking** - Success/failure rates and performance metrics  
✅ **Error Handling** - Comprehensive error detection and recovery  
✅ **Detailed Logging** - File and console logging for troubleshooting  
✅ **Remote Control** - Control lockers from any network-connected device

### Use Cases

- **Automated Delivery Systems** - Package handling with robotic assistance
- **Smart Storage Solutions** - Coordinated locker and robot operations
- **Laboratory Automation** - Sample handling and storage
- **Industrial Testing** - Endurance testing of locker-robot systems

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAPTOP (Control Station)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Main Cycle Controller (main.py)                 │  │
│  │  • Orchestrates all operations                            │  │
│  │  • Runs continuous cycles                                 │  │
│  │  • Tracks statistics                                      │  │
│  │  • Provides web interface (port 9091)                     │  │
│  └────────────┬────────────────────────────────┬─────────────┘  │
│               │                                 │                │
│      ┌────────▼─────────┐            ┌─────────▼────────┐      │
│      │  Locker Client   │            │ Robot Controller │      │
│      │ (locker_client)  │            │ (robot_controller)│      │
│      └────────┬─────────┘            └─────────┬────────┘      │
└───────────────┼───────────────────────────────┼────────────────┘
                │                                 │
        Network │ (HTTP)                  Network │ (TCP/IP)
                │                                 │
    ┌───────────▼──────────┐          ┌──────────▼──────────┐
    │   Locker Server      │          │   Fairino Robot     │
    │   72.61.181.1:8080   │          │   192.168.58.101    │
    │                      │          │                     │
    │  • Controls 12       │          │  • 6-axis robot arm │
    │    lockers           │          │  • Predefined       │
    │  • Door sensors      │          │    positions        │
    │  • IR sensors        │          │  • SDK feedback     │
    └──────────────────────┘          └─────────────────────┘
```

### Network Configuration

| Component | IP Address | Port | Protocol |
|-----------|-----------|------|----------|
| Locker Server | 72.61.181.1 | 8080 | HTTP/REST |
| Robot Controller | 192.168.58.101 | (SDK) | TCP/IP |
| Web Monitor | localhost | 9091 | HTTP |

---

## 🔧 Hardware Components

### 1. Smart Locker System

**Location:** 72.61.181.1:8080

**Specifications:**
- **Number of Lockers:** 12 (numbered 1-12)
- **Door Sensors:** Magnetic contact sensors (detect open/closed state)
- **IR Sensors:** Infrared sensors (detect empty/occupied state)
- **Control:** Electronic locks with remote actuation
- **Server:** REST API server running on embedded system

**Locker States:**
- **Door Status:** Open / Closed
- **Sensor Status:** Empty / Occupied / Unknown

### 2. Fairino Robot Arm

**Location:** 192.168.58.101

**Specifications:**
- **Type:** 6-axis industrial robot arm
- **SDK:** Fairino Robot SDK (Python)
- **Control Method:** Joint angle positioning
- **Communication:** TCP/IP network connection
- **Feedback:** Real-time position feedback via SDK

**Predefined Positions (Joint Angles in Degrees):**
```python
'home':       [80.555, -111.609, 110.737, -188.994, -84.695, 144.436]
'position_1': [80.555, -91.025,  126.989, -188.994, -84.695, 144.436]
```

---

## 💻 Software Components

### Component Structure

```
locker-robot-system/
│
├── main.py                      # Main cycle controller (orchestrator)
├── locker_client.py             # Locker control library
├── robot_controller.py          # Robot control library
├── single_locker_server.py      # Locker server (runs on 72.61.181.1)
├── test_locker_client.py        # Example usage scripts
│
└── cycle_controller.log         # Detailed operation logs (generated)
```

### 1. Main Cycle Controller (`main.py`)

**Purpose:** Orchestrates the complete system operation

**Key Classes:**
- `CycleController` - Main controller managing cycle execution

**Responsibilities:**
- Initialize locker client and robot controller
- Execute continuous cycles
- Verify state changes (CLOSED → OPEN → CLOSED)
- Track statistics (success/failure counts)
- Provide web monitoring interface
- Handle errors and reconnections

**Key Configuration Parameters:**
```python
MAIN_SERVER_IP = "72.61.181.1"      # Locker server IP
MAIN_SERVER_PORT = 8080              # Locker server port
MONITOR_PORT = 9091                  # Web interface port
TARGET_LOCKER = 1                    # Locker to use (1-12)
ROBOT_IP = "192.168.58.101"         # Robot IP address

LOCKER_OPEN_TIMEOUT = 10             # Timeout for locker open (seconds)
LOCKER_CLOSE_TIMEOUT = 30            # Timeout for locker close (seconds)
MAX_OPEN_RETRIES = 3                 # Max retries for opening locker
RETRY_DELAY = 2                      # Delay between retries (seconds)
```

### 2. Locker Client (`locker_client.py`)

**Purpose:** Python library for controlling smart lockers remotely

**Key Class:**
- `LockerClient` - Main client for locker operations

**Authentication:**
- Password: `Cyber@Abed1102`
- Session-based authentication (cookie-based)

**Core Methods:**
```python
# Simple API (recommended for integration)
openLocker(locker_num)              # Open specific locker
lockerStatus(locker_num)            # Get door status ("Open"/"Closed"/"Unknown")
sensorStatus(locker_num)            # Get sensor status ("Empty"/"Occupied"/"Unknown")

# Detailed API
open_locker(locker_num)             # Open with detailed response
open_multiple_lockers(list)         # Open multiple lockers
get_status()                        # Get full system status
get_locker_status(locker_num)       # Get specific locker status
wait_for_locker_close(locker_num)   # Wait for locker to close
```

**Example Usage:**
```python
from locker_client import LockerClient

# Connect to server
client = LockerClient()

# Open locker 2
if client.openLocker(2):
    print("Locker opened!")

# Check status
door = client.lockerStatus(2)      # Returns: "Open", "Closed", or "Unknown"
sensor = client.sensorStatus(2)    # Returns: "Empty", "Occupied", or "Unknown"
```

### 3. Robot Controller (`robot_controller.py`)

**Purpose:** Control Fairino robot arm with SDK feedback

**Key Class:**
- `SimpleRobotController` - Complete robot control with motion sequences

**Configuration Parameters:**
```python
INTER_MOVEMENT_DELAY = 0.0          # Delay between movements (seconds)
FEEDBACK_CHECK_INTERVAL = 0.1       # SDK feedback polling interval
RECONNECT_DELAY = 1.0               # Reconnection attempt delay
MOVEMENT_SPEED = 20.0               # Movement velocity (0-100%)
MOVEMENT_ACCELERATION = 100.0       # Movement acceleration (0-100%)
```

**Core Methods:**
```python
connect_to_robot()                  # Connect to robot with retry
move_to_position(position_name)     # Move to predefined position
execute_motion_sequence()           # Execute complete sequence: home→position_1→home
get_robot_feedback()                # Get current joint positions
verify_position_reached()           # Verify position with tolerance
stop_movement()                     # Emergency stop
```

**Motion Sequence:**
1. **Home Position** - Starting/ending position
2. **Position 1** - Target position
3. **Home Position** - Return to start

**Safety Features:**
- SDK-based motion verification (no artificial delays)
- Blocking commands (waits for motion completion)
- Position verification with tolerance (±2.0°)
- Emergency stop capability
- Automatic reconnection on failure

---

## 📦 Installation & Setup

### Prerequisites

**Software Requirements:**
- Python 3.7 or higher
- pip package manager
- Network connectivity to locker server and robot

**Hardware Requirements:**
- Laptop/computer for running control software
- Network access to 72.61.181.1 (locker server)
- Network access to 192.168.58.101 (robot)

### Step 1: Install Python Dependencies

```bash
# Install required packages
pip install requests fairino

# Or create requirements.txt:
# requests>=2.28.0
# fairino>=1.0.0

pip install -r requirements.txt
```

### Step 2: Verify Network Connectivity

```bash
# Test locker server connectivity
ping 72.61.181.1

# Test locker server API
curl http://72.61.181.1:8080/api/status

# Test robot connectivity
ping 192.168.58.101
```

### Step 3: Configure System

Edit configuration parameters in `main.py`:

```python
# Update these if your network configuration is different
MAIN_SERVER_IP = "72.61.181.1"      # Your locker server IP
ROBOT_IP = "192.168.58.101"         # Your robot IP
TARGET_LOCKER = 1                    # Locker number to use (1-12)
```

### Step 4: Test Individual Components

**Test Locker Client:**
```bash
python test_locker_client.py
```

**Test Robot Controller:**
```bash
python robot_controller.py
```

### Step 5: Run Main System

```bash
python main.py
```

**Expected Output:**
```
============================================================
🤖 LOCKER-ROBOT CYCLE CONTROLLER
============================================================
Server: 72.61.181.1:8080
Robot: 192.168.58.101
Target Locker: #1
Web Interface: http://localhost:9091
Detailed Logs: cycle_controller.log
============================================================

✅ System ready!
🌐 Open browser: http://localhost:9091
📊 Monitor cycles in real-time

🛑 Press Ctrl+C to stop
============================================================
```

---

## ⚙️ Configuration Guide

### Main Controller Configuration (`main.py`)

#### Network Settings

```python
MAIN_SERVER_IP = "72.61.181.1"      # Locker server IP address
MAIN_SERVER_PORT = 8080              # Locker server port
ROBOT_IP = "192.168.58.101"         # Robot IP address
MONITOR_PORT = 9091                  # Web monitoring interface port
TARGET_LOCKER = 1                    # Which locker to use (1-12)
```

#### Timeout Settings

```python
LOCKER_OPEN_TIMEOUT = 10    # Maximum time to wait for locker to open (seconds)
LOCKER_CLOSE_TIMEOUT = 30   # Maximum time to wait for locker to close (seconds)
```

**Recommendations:**
- Open timeout: 5-15 seconds (depends on locker mechanism speed)
- Close timeout: 20-60 seconds (allow time for user to close door)

#### Retry Settings

```python
MAX_OPEN_RETRIES = 3        # How many times to retry opening locker
RETRY_DELAY = 2             # Delay between retry attempts (seconds)
```

**Recommendations:**
- 2-5 retries for production
- 1-3 seconds delay between retries

#### Logging Settings

```python
LOG_FILE = "cycle_controller.log"   # Log file path
```

Logs are automatically rotated. Both file (detailed) and console (summary) logging are available.

### Robot Controller Configuration (`robot_controller.py`)

```python
INTER_MOVEMENT_DELAY = 0.0          # Delay between sequence steps (0.0 for immediate)
FEEDBACK_CHECK_INTERVAL = 0.1       # SDK feedback polling interval
RECONNECT_DELAY = 1.0               # Delay between reconnection attempts

MOVEMENT_SPEED = 20.0               # Movement velocity (0-100%)
MOVEMENT_ACCELERATION = 100.0       # Movement acceleration (0-100%)
```

**Speed Recommendations:**
- Slow/Careful: 10-20%
- Normal: 20-40%
- Fast: 40-60%
- Maximum: 60-100% (use with caution)

### Locker Client Configuration (`locker_client.py`)

```python
server_ip = "72.61.181.1"           # Server IP
port = 8080                          # Server port
password = "Cyber@Abed1102"         # Authentication password
```

---

## 📖 Usage Guide

### Basic Usage - Running the System

1. **Start the Main Controller:**
```bash
python main.py
```

2. **Open Web Monitoring Interface:**
- Open browser to `http://localhost:9091`
- View real-time cycle status
- Monitor success/failure statistics

3. **Stop the System:**
- Press `Ctrl+C` in the terminal
- System will display final statistics
- Graceful shutdown with data preservation

### Console Output

**During Operation:**
```
[2025-11-15 14:30:15] CYCLE #1 STARTED
[2025-11-15 14:30:47] CYCLE #1 COMPLETED in 32.45s ✅

[2025-11-15 14:30:47] CYCLE #2 STARTED
[2025-11-15 14:31:19] CYCLE #2 COMPLETED in 31.89s ✅

[2025-11-15 14:31:19] CYCLE #3 STARTED
[2025-11-15 14:31:35] CYCLE #3 FAILED ❌
```

**On Shutdown (Ctrl+C):**
```
🛑 Shutting down controller...

================================================================================
                    FINAL STATISTICS SUMMARY
================================================================================
Total Runtime:        02:15:34 (HH:MM:SS)
Total Cycles:         127
✅ Successful Cycles: 125
❌ Failed Cycles:     2
Success Rate:         98.4%
================================================================================

✅ Controller stopped gracefully
============================================================
```

### Using Individual Components

#### Locker Client Only

```python
from locker_client import LockerClient

# Create client
client = LockerClient()

# Open single locker
client.openLocker(5)

# Check door status
status = client.lockerStatus(5)
print(f"Locker 5 door is: {status}")  # "Open", "Closed", or "Unknown"

# Check if empty
sensor = client.sensorStatus(5)
print(f"Locker 5 is: {sensor}")  # "Empty", "Occupied", or "Unknown"

# Open multiple lockers
client.open_multiple_lockers([1, 3, 5, 7])

# Get full system status
status = client.get_status()
client.print_status()
```

#### Robot Controller Only

```python
from robot_controller import SimpleRobotController

# Create controller
robot = SimpleRobotController(robot_ip='192.168.58.101')

# Execute motion sequence
success = robot.execute_motion_sequence()

if success:
    print("Motion sequence completed successfully!")
else:
    print("Motion sequence failed!")

# Get current position
current_pos = robot.get_robot_feedback()
print(f"Current joint angles: {current_pos}")

# Disconnect
robot.disconnect()
```

---

## 🔌 API Reference

### Locker Client API

#### `LockerClient(server_ip, port, password)`
Initialize locker client connection.

**Parameters:**
- `server_ip` (str): Server IP address (default: "72.61.181.1")
- `port` (int): Server port (default: 8080)
- `password` (str): Authentication password (default: "Cyber@Abed1102")

**Example:**
```python
client = LockerClient()
# or
client = LockerClient(server_ip="192.168.1.100", port=8080)
```

#### `openLocker(locker_num)`
Open specific locker.

**Parameters:**
- `locker_num` (int): Locker number (1-12)

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = client.openLocker(2)
```

#### `lockerStatus(locker_num)`
Get locker door status.

**Parameters:**
- `locker_num` (int): Locker number (1-12)

**Returns:**
- `str`: "Open", "Closed", or "Unknown"

**Example:**
```python
status = client.lockerStatus(2)
if status == "Open":
    print("Door is open")
```

#### `sensorStatus(locker_num)`
Get locker IR sensor status.

**Parameters:**
- `locker_num` (int): Locker number (1-12)

**Returns:**
- `str`: "Empty", "Occupied", or "Unknown"

**Example:**
```python
sensor = client.sensorStatus(2)
if sensor == "Empty":
    print("Locker is empty")
```

#### `get_status()`
Get complete system status.

**Returns:**
- `dict`: System status including all lockers

**Response Structure:**
```python
{
    'connected': True,
    'uptime': 3600,
    'total_commands': 127,
    'lockers': {
        '1': {'door_open': False, 'sensor_status': 'Empty'},
        '2': {'door_open': True, 'sensor_status': 'Occupied'},
        # ... (lockers 3-12)
    }
}
```

### Robot Controller API

#### `SimpleRobotController(robot_ip)`
Initialize robot controller.

**Parameters:**
- `robot_ip` (str): Robot IP address (default: '192.168.58.101')

**Example:**
```python
robot = SimpleRobotController(robot_ip='192.168.58.101')
```

#### `execute_motion_sequence()`
Execute complete motion sequence: home → position_1 → home

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = robot.execute_motion_sequence()
```

#### `move_to_position(position_name)`
Move robot to predefined position.

**Parameters:**
- `position_name` (str): Position name ('home', 'position_1')

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
robot.move_to_position('home')
```

#### `get_robot_feedback()`
Get current robot joint positions.

**Returns:**
- `list`: Joint angles in degrees [J1, J2, J3, J4, J5, J6]
- `None`: If feedback unavailable

**Example:**
```python
angles = robot.get_robot_feedback()
print(f"Current angles: {angles}")
```

#### `stop_movement()`
Emergency stop - immediately halt all robot movement.

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
robot.stop_movement()
```

### Cycle Controller API

#### `get_status()`
Get current system status from cycle controller.

**Returns:**
```python
{
    'running': True,
    'cycle_count': 127,
    'successful_cycles': 125,
    'failed_cycles': 2,
    'server_connected': True,
    'robot_connected': True,
    'current_cycle': {
        'cycle_num': 127,
        'phase': 'Complete',
        'locker_status': 'CLOSED',
        'robot_status': 'COMPLETED',
        'status': 'Success',
        'timestamp': '2025-11-15T14:30:47',
        'error': None,
        'duration': 32.45
    },
    'recent_cycles': [...]  # Last 10 cycles
}
```

---

## 🔄 Cycle Flow & Logic

### Complete Cycle Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 0: Check Initial State                               │
│  ✓ Verify locker is CLOSED                                  │
│  ✓ Cannot proceed if locker is not CLOSED                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PHASE 1: Check Connection                                   │
│  ✓ Verify server connection                                 │
│  ✓ Ensure communication is active                           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PHASE 2: Open Locker                                        │
│  ✓ Send open command to locker                              │
│  ✓ Retry up to MAX_OPEN_RETRIES times if needed            │
│  ✓ Delay RETRY_DELAY seconds between retries               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PHASE 3: Verify State Change (CLOSED → OPEN)               │
│  ✓ Poll locker status every 0.5 seconds                     │
│  ✓ Wait up to LOCKER_OPEN_TIMEOUT seconds                   │
│  ✓ Confirm locker changed from CLOSED to OPEN               │
│  ❌ FAIL if timeout or state doesn't change                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PHASE 4: Execute Robot Sequence                             │
│  ✓ Safety check: Verify locker is OPEN                      │
│  ✓ Execute: home → position_1 → home                        │
│  ✓ Use SDK feedback for motion verification                 │
│  ✓ No artificial delays (blocking SDK commands)             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PHASE 5: Verify State Change (OPEN → CLOSED)               │
│  ✓ Poll locker status every 0.5 seconds                     │
│  ✓ Wait up to LOCKER_CLOSE_TIMEOUT seconds                  │
│  ✓ Confirm locker changed from OPEN to CLOSED               │
│  ❌ CRITICAL FAILURE if timeout (no retries!)                │
│  ⚠️  Requires physical inspection if fails                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  CYCLE COMPLETE                                              │
│  ✅ Success: Log statistics and start next cycle             │
│  ❌ Failure: Log error and start next cycle                  │
└─────────────────────────────────────────────────────────────┘
```

### State Verification Rules

**STRICT LOGIC - NO SHORTCUTS:**

1. **Initial State Check:**
   - Locker MUST be CLOSED before cycle starts
   - Cannot start cycle if locker is OPEN
   - Prevents unsafe operations

2. **Open Verification:**
   - Must detect state change: CLOSED → OPEN
   - Timeout: LOCKER_OPEN_TIMEOUT seconds
   - Retries: Up to MAX_OPEN_RETRIES attempts
   - Failure → Cycle fails, next cycle starts

3. **Robot Execution:**
   - ONLY executes when locker is verified OPEN
   - Safety check before motion
   - Uses SDK feedback (no delays)
   - Blocking commands wait for completion

4. **Close Verification:**
   - Must detect state change: OPEN → CLOSED
   - Timeout: LOCKER_CLOSE_TIMEOUT seconds
   - **NO RETRIES** (safety critical)
   - Failure → CRITICAL - requires physical inspection

### Error Handling

**Error Types:**

1. **Connection Errors:**
   - Auto-reconnection attempts
   - 5-second delay between attempts
   - Continues cycle when reconnected

2. **State Verification Failures:**
   - Logged in detail
   - Cycle marked as failed
   - Next cycle starts automatically

3. **Critical Failures:**
   - Locker won't close → STOPS operations
   - Requires physical inspection
   - Logged as CRITICAL error

---

## 🖥️ Web Monitoring Interface

### Accessing the Interface

**URL:** `http://localhost:9091`

Open in any modern web browser after starting `main.py`.

### Dashboard Features

#### 1. System Status Card
Shows real-time connection status:
- **Server Status:** 🟢 Connected / 🔴 Disconnected
- **Robot Status:** 🟢 Connected / 🔴 Disconnected

#### 2. Cycle Count Display
Large display showing:
- **Total Cycles Executed**
- **✅ Successful Cycles**
- **❌ Failed Cycles**

#### 3. Current Cycle Status
Real-time information:
- **Current Phase:** Which phase is executing
- **Locker Status:** 🔓 OPEN / 🔒 CLOSED / ❓ Unknown
- **Robot Status:** ✅ Completed / ⚙️ In Progress / ⏳ Waiting
- **Cycle Status:** ✅ Success / ❌ Failed / ⏳ In Progress
- **Duration:** Time elapsed for current cycle

#### 4. Error Display
Shows current error message if cycle fails.

#### 5. Cycle History
Last 10 cycles with:
- Cycle number
- Final phase
- Success/Failed status
- Duration

### Auto-Refresh

Interface updates automatically every 1 second via AJAX polling to `/api/status` endpoint.

### Screenshots

**Normal Operation:**
```
┌──────────────────────────────────────────┐
│   🤖 Locker-Robot Cycle Controller      │
├──────────────────────────────────────────┤
│  System Status                           │
│  Server: 🟢    Robot: 🟢                 │
├──────────────────────────────────────────┤
│         CYCLE COUNT: 127                 │
│    ✅ Success: 125    ❌ Failed: 2       │
├──────────────────────────────────────────┤
│  Current Cycle Status                    │
│  Phase: Verifying Close State            │
│  Locker: 🔓 OPEN                         │
│  Robot: ✅ COMPLETED                     │
│  Status: ⏳ In Progress                  │
│  Duration: 28.3s                         │
└──────────────────────────────────────────┘
```

---

## 🛡️ Safety Features

### 1. State Verification

**Double Verification:**
- Every state change is verified
- CLOSED → OPEN verification
- OPEN → CLOSED verification
- Prevents unsafe operations

### 2. Safety Checks

**Robot Execution Safety:**
```python
# Before robot moves, system verifies:
if locker_status != "Open":
    # ABORT - Do not execute robot sequence
    return False
```

### 3. Critical Failure Handling

**Locker Won't Close:**
- Marked as CRITICAL error
- NO automatic retries (safety)
- Requires physical inspection
- System logs detailed error
- Next cycle does NOT start automatically

### 4. Emergency Stop

**Robot Emergency Stop:**
```python
robot.stop_movement()  # Immediately halts all movement
```

**Manual Intervention:**
- Press `Ctrl+C` to stop system
- Graceful shutdown
- Statistics preserved
- Clean disconnection

### 5. Timeout Protection

**Prevents Infinite Waiting:**
- Open timeout: 10 seconds
- Close timeout: 30 seconds
- Reconnection timeout: Configured per component

### 6. Connection Monitoring

**Continuous Monitoring:**
- Server connection checked every cycle
- Robot connection verified before motion
- Auto-reconnection on disconnection
- Status visible in web interface

### 7. Detailed Logging

**Forensic Analysis:**
- Every operation logged
- Timestamps for all events
- Error details captured
- Success/failure tracking
- File: `cycle_controller.log`

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Issue 1: Cannot Connect to Locker Server

**Symptoms:**
```
❌ Cannot connect to server: http://72.61.181.1:8080
```

**Solutions:**
1. Verify server IP address:
   ```bash
   ping 72.61.181.1
   ```

2. Check server is running on port 8080:
   ```bash
   curl http://72.61.181.1:8080/api/status
   ```

3. Verify firewall allows connection

4. Check password is correct in `locker_client.py`:
   ```python
   password = "Cyber@Abed1102"
   ```

#### Issue 2: Cannot Connect to Robot

**Symptoms:**
```
❌ Failed to connect to robot: 192.168.58.101
```

**Solutions:**
1. Verify robot IP address:
   ```bash
   ping 192.168.58.101
   ```

2. Ensure robot is powered on

3. Check robot is not in emergency stop mode

4. Verify Fairino SDK is installed:
   ```bash
   pip install fairino
   ```

5. Check robot network settings match your configuration

#### Issue 3: Locker Won't Open

**Symptoms:**
```
❌ Failed to open locker after retries
```

**Solutions:**
1. Check locker hardware:
   - Is locker physically stuck?
   - Is lock mechanism working?
   - Check power to locker

2. Verify locker number is correct (1-12)

3. Try opening different locker to isolate issue

4. Check locker server logs

5. Increase `MAX_OPEN_RETRIES` in configuration

#### Issue 4: Locker Won't Close (CRITICAL)

**Symptoms:**
```
❌ CRITICAL: Locker DID NOT CLOSE within 30s
❌ This cycle FAILED - NO RETRIES - PHYSICAL INSPECTION REQUIRED
```

**Solutions:**
1. **Immediate Action:**
   - Physically inspect locker
   - Check for obstructions
   - Verify door closes manually

2. Check door sensor:
   - Is sensor working?
   - Clean sensor contacts
   - Test sensor independently

3. Verify nothing blocking door

4. Check locker mechanism

5. Adjust `LOCKER_CLOSE_TIMEOUT` if needed (for testing)

#### Issue 5: Robot Motion Fails

**Symptoms:**
```
❌ Robot sequence execution failed
```

**Solutions:**
1. Check robot connection

2. Verify robot is not in error state:
   ```python
   robot.get_robot_feedback()
   ```

3. Check robot workspace:
   - No obstacles
   - Safe to move to positions
   - Within reach limits

4. Verify position definitions in `robot_controller.py`

5. Test individual movements:
   ```python
   robot.move_to_position('home')
   ```

#### Issue 6: High Failure Rate

**Symptoms:**
```
Success Rate: 45.2%  (Many failures)
```

**Solutions:**
1. **Check Timeouts:**
   - Increase `LOCKER_OPEN_TIMEOUT`
   - Increase `LOCKER_CLOSE_TIMEOUT`

2. **Check Network:**
   - Network stability
   - Latency to servers
   - Packet loss

3. **Check Hardware:**
   - Locker mechanism speed
   - Door sensor reliability
   - Robot positioning accuracy

4. **Review Logs:**
   - Identify failure patterns
   - Check error messages
   - Look for specific phases failing

#### Issue 7: Web Interface Not Loading

**Symptoms:**
```
Cannot access http://localhost:9091
```

**Solutions:**
1. Verify `main.py` is running

2. Check console output for:
   ```
   ✅ System ready!
   🌐 Open browser: http://localhost:9091
   ```

3. Try `http://127.0.0.1:9091` instead

4. Check port 9091 not in use:
   ```bash
   netstat -an | grep 9091
   ```

5. Change `MONITOR_PORT` if needed

### Log Analysis

**View Detailed Logs:**
```bash
tail -f cycle_controller.log
```

**Search for Errors:**
```bash
grep "ERROR" cycle_controller.log
grep "CRITICAL" cycle_controller.log
grep "FAILED" cycle_controller.log
```

**View Specific Cycle:**
```bash
grep "CYCLE #127" cycle_controller.log
```

### Debug Mode

Enable more detailed logging by modifying log level:

```python
self.file_logger.setLevel(logging.DEBUG)  # Change from INFO to DEBUG
```

---

## 📝 Code Examples

### Example 1: Simple Locker Control

```python
#!/usr/bin/env python3
"""
Simple example: Open locker, check status, wait for close
"""

from locker_client import LockerClient
import time

# Connect to locker system
client = LockerClient()

# Open locker 3
locker_num = 3
print(f"Opening locker {locker_num}...")

if client.openLocker(locker_num):
    print("✅ Locker opened successfully!")
    
    # Check door status
    door = client.lockerStatus(locker_num)
    print(f"Door status: {door}")
    
    # Wait for user to close door
    print("Waiting for locker to close...")
    closed = client.wait_for_locker_close(locker_num, timeout=30)
    
    if closed:
        print("✅ Locker closed!")
    else:
        print("⏰ Timeout - locker still open")
else:
    print("❌ Failed to open locker")
```

### Example 2: Open Empty Lockers Only

```python
#!/usr/bin/env python3
"""
Open all empty lockers
"""

from locker_client import LockerClient

client = LockerClient()

print("Checking all lockers...")

for locker_num in range(1, 13):  # Lockers 1-12
    door = client.lockerStatus(locker_num)
    sensor = client.sensorStatus(locker_num)
    
    print(f"\nLocker {locker_num}:")
    print(f"  Door: {door}")
    print(f"  Sensor: {sensor}")
    
    # Open if closed and empty
    if door == "Closed" and sensor == "Empty":
        print(f"  → Opening locker {locker_num}...")
        client.openLocker(locker_num)
    else:
        print(f"  → Skipping (not empty or already open)")
```

### Example 3: Robot Motion Test

```python
#!/usr/bin/env python3
"""
Test robot motion sequence
"""

from robot_controller import SimpleRobotController

# Connect to robot
robot = SimpleRobotController(robot_ip='192.168.58.101')

# Get current position
print("Current position:")
current = robot.get_robot_feedback()
print(current)

# Execute motion sequence
print("\nExecuting motion sequence...")
success = robot.execute_motion_sequence()

if success:
    print("✅ Motion sequence completed successfully!")
else:
    print("❌ Motion sequence failed!")

# Get final position
print("\nFinal position:")
final = robot.get_robot_feedback()
print(final)

# Disconnect
robot.disconnect()
```

### Example 4: Custom Cycle with Callback

```python
#!/usr/bin/env python3
"""
Custom cycle with callback function
"""

from locker_client import LockerClient
from robot_controller import SimpleRobotController
import time

def my_custom_action():
    """Custom action to perform during cycle"""
    print("🎯 Performing custom action...")
    time.sleep(2)
    print("✅ Custom action complete")

# Initialize components
locker = LockerClient()
robot = SimpleRobotController()

locker_num = 1

# Open locker
print("1. Opening locker...")
locker.openLocker(locker_num)

# Wait for locker to open
time.sleep(2)

# Verify opened
if locker.lockerStatus(locker_num) == "Open":
    print("✅ Locker is open")
    
    # Execute robot motion
    print("\n2. Executing robot motion...")
    robot.execute_motion_sequence()
    
    # Custom action
    print("\n3. Custom action...")
    my_custom_action()
    
    # Wait for locker to close
    print("\n4. Waiting for locker to close...")
    locker.wait_for_locker_close(locker_num, timeout=30)
    
    print("\n✅ Cycle complete!")
else:
    print("❌ Failed to open locker")
```

### Example 5: Statistics Monitoring

```python
#!/usr/bin/env python3
"""
Monitor system statistics via API
"""

import requests
import time
import json

MONITOR_URL = "http://localhost:9091/api/status"

while True:
    try:
        # Get status from API
        response = requests.get(MONITOR_URL)
        data = response.json()
        
        # Display statistics
        print("\n" + "="*50)
        print(f"Cycle Count: {data['cycle_count']}")
        print(f"✅ Successful: {data['successful_cycles']}")
        print(f"❌ Failed: {data['failed_cycles']}")
        
        # Calculate success rate
        total = data['successful_cycles'] + data['failed_cycles']
        if total > 0:
            rate = (data['successful_cycles'] / total) * 100
            print(f"Success Rate: {rate:.1f}%")
        
        # Current cycle info
        cycle = data['current_cycle']
        print(f"\nCurrent Cycle #{cycle['cycle_num']}:")
        print(f"  Phase: {cycle['phase']}")
        print(f"  Status: {cycle['status']}")
        print(f"  Duration: {cycle['duration']:.1f}s")
        
        if cycle['error']:
            print(f"  ⚠️ Error: {cycle['error']}")
        
        # Wait before next update
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
```

---

## 📊 Performance & Statistics

### Metrics Tracked

The system tracks the following metrics:

1. **Cycle Count** - Total number of cycles executed
2. **Successful Cycles** - Cycles that completed successfully
3. **Failed Cycles** - Cycles that encountered errors
4. **Success Rate** - Percentage of successful cycles
5. **Cycle Duration** - Time taken for each cycle
6. **Total Runtime** - Total system uptime

### Viewing Statistics

**Real-time (Web Interface):**
- Visit `http://localhost:9091`
- View live statistics in dashboard

**On Shutdown:**
- Press `Ctrl+C`
- View summary in console

**From Logs:**
```bash
grep "Statistics" cycle_controller.log
```

### Typical Performance

**Expected Cycle Times:**

| Phase | Typical Duration |
|-------|-----------------|
| Check Initial State | 0.5 - 1.0 seconds |
| Check Connection | 0.1 - 0.5 seconds |
| Open Locker | 1.0 - 3.0 seconds |
| Verify Open | 2.0 - 5.0 seconds |
| Robot Sequence | 15.0 - 25.0 seconds |
| Verify Close | 5.0 - 20.0 seconds |
| **Total Cycle** | **25 - 55 seconds** |

**Success Rate:**
- **Target:** >95%
- **Good:** 90-95%
- **Acceptable:** 85-90%
- **Poor:** <85% (investigate issues)

### Optimization Tips

1. **Reduce Timeouts** (if safe):
   - Lower `LOCKER_OPEN_TIMEOUT`
   - Lower `LOCKER_CLOSE_TIMEOUT`

2. **Increase Robot Speed** (if safe):
   - Increase `MOVEMENT_SPEED` in robot_controller.py

3. **Reduce Delays:**
   - Set `INTER_MOVEMENT_DELAY = 0.0`

4. **Hardware Improvements:**
   - Faster locker mechanisms
   - Better door sensors
   - Network optimization

---

## 🚀 Advanced Topics

### Custom Positions

Add new robot positions in `robot_controller.py`:

```python
self.positions = {
    'home': [80.555, -111.609, 110.737, -188.994, -84.695, 144.436],
    'position_1': [80.555, -91.025, 126.989, -188.994, -84.695, 144.436],
    'position_2': [80.555, -111.609, 110.737, -188.994, -84.695, 144.436],
    # Add your custom position:
    'custom_position': [90.0, -100.0, 120.0, -180.0, -90.0, 150.0],
}
```

Then use:
```python
robot.move_to_position('custom_position')
```

### Multiple Lockers

Modify `main.py` to cycle through multiple lockers:

```python
TARGET_LOCKERS = [1, 2, 3]  # Use multiple lockers

# In cycle execution:
for locker_num in TARGET_LOCKERS:
    # Execute cycle for this locker
    self._execute_cycle_for_locker(locker_num)
```

### Data Export

Export statistics to CSV:

```python
import csv

def export_statistics(self):
    """Export cycle history to CSV"""
    with open('cycle_history.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Status', 'Duration', 'Phase', 'Error', 'Timestamp'])
        
        for cycle in self.cycle_history:
            writer.writerow([
                cycle['cycle_num'],
                cycle['status'],
                cycle['duration'],
                cycle['phase'],
                cycle['error'] or '',
                cycle['timestamp']
            ])
```

### Email Notifications

Add email alerts for failures:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(self, cycle_num, error):
    """Send email alert on critical failure"""
    msg = MIMEText(f"Cycle #{cycle_num} failed: {error}")
    msg['Subject'] = f'⚠️ Locker-Robot System Alert - Cycle #{cycle_num} Failed'
    msg['From'] = 'system@example.com'
    msg['To'] = 'admin@example.com'
    
    with smtplib.SMTP('localhost') as server:
        server.send_message(msg)
```

### Database Integration

Store cycle data in SQLite:

```python
import sqlite3

def init_database(self):
    """Initialize database for cycle tracking"""
    conn = sqlite3.connect('cycles.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            cycle_num INTEGER PRIMARY KEY,
            status TEXT,
            duration REAL,
            phase TEXT,
            error TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_cycle_to_db(self, cycle_data):
    """Save cycle to database"""
    conn = sqlite3.connect('cycles.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        cycle_data['cycle_num'],
        cycle_data['status'],
        cycle_data['duration'],
        cycle_data['phase'],
        cycle_data['error'],
        cycle_data['timestamp']
    ))
    conn.commit()
    conn.close()
```

### Remote Monitoring

Access web interface remotely:

Change in `main.py`:
```python
server = HTTPServer(('0.0.0.0', MONITOR_PORT), MonitorHandler)
```

Access from other devices:
```
http://YOUR_LAPTOP_IP:9091
```

### REST API Extension

Add custom API endpoints:

```python
def do_GET(self):
    if self.path == '/api/statistics':
        # Custom statistics endpoint
        stats = {
            'total_cycles': controller.cycle_count,
            'success_count': controller.successful_cycles,
            'failed_count': controller.failed_cycles,
            'success_rate': (controller.successful_cycles / controller.cycle_count * 100) if controller.cycle_count > 0 else 0
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
```

---

## 📄 File Structure Summary

```
locker-robot-system/
│
├── main.py                          # Main cycle controller
│   ├── CycleController class
│   ├── MonitorHandler class
│   ├── Web interface HTML/CSS/JS
│   └── Main execution loop
│
├── locker_client.py                 # Locker control library
│   ├── LockerClient class
│   ├── Simple API (openLocker, lockerStatus, sensorStatus)
│   ├── Detailed API (open_locker, get_status, etc.)
│   └── Example functions
│
├── robot_controller.py              # Robot control library
│   ├── SimpleRobotController class
│   ├── Motion sequence execution
│   ├── SDK feedback integration
│   └── Position verification
│
├── single_locker_server.py         # Locker server (runs on 72.61.181.1)
│   └── REST API for locker control
│
├── test_locker_client.py           # Example usage scripts
│   └── Basic usage examples
│
└── cycle_controller.log             # Generated log file
    └── Detailed operation logs
```

---

## 🎓 Learning Resources

### Understanding the Code

**Start Here:**
1. Read `test_locker_client.py` - Simple examples
2. Study `locker_client.py` - API documentation
3. Review `robot_controller.py` - Robot control
4. Understand `main.py` - System integration

### Key Concepts

**State Verification:**
- Why we verify CLOSED → OPEN → CLOSED
- Safety implications
- Timeout handling

**Blocking vs Non-Blocking:**
- Robot SDK uses blocking commands
- Advantages of SDK feedback
- Why we don't use artificial delays

**Error Recovery:**
- Automatic reconnection
- Retry mechanisms
- When to fail vs continue

### Debugging Tips

1. **Enable DEBUG logging**
2. **Use web interface** for real-time monitoring
3. **Check logs** for detailed error messages
4. **Test components individually** before integration
5. **Use try-except** blocks during development

---

## ⚡ Quick Reference

### Essential Commands

```bash
# Run main system
python main.py

# Test locker client
python test_locker_client.py

# Test robot controller
python robot_controller.py

# View logs
tail -f cycle_controller.log

# Monitor web interface
# Open: http://localhost:9091
```

### Essential Configuration

```python
# main.py
TARGET_LOCKER = 1                    # Locker to use
LOCKER_OPEN_TIMEOUT = 10             # Open timeout
LOCKER_CLOSE_TIMEOUT = 30            # Close timeout
MAX_OPEN_RETRIES = 3                 # Open retries

# robot_controller.py
MOVEMENT_SPEED = 20.0                # Robot speed (%)
INTER_MOVEMENT_DELAY = 0.0           # Delay between moves
```

### Essential API

```python
# Locker Client
client.openLocker(num)               # Open locker
client.lockerStatus(num)             # Get door status
client.sensorStatus(num)             # Get sensor status

# Robot Controller
robot.execute_motion_sequence()      # Run sequence
robot.move_to_position(name)         # Move to position
robot.stop_movement()                # Emergency stop
```

---

## 📞 Support & Contact

### Getting Help

1. **Check Documentation** - This README
2. **Review Logs** - `cycle_controller.log`
3. **Test Components** - Individual component testing
4. **Check Network** - Verify connectivity

### Common Resources

- **Fairino Robot SDK Documentation**
- **Python Requests Library Documentation**
- **HTTP REST API Basics**

---

## 📋 Appendix

### A. Port Reference

| Port | Service | Purpose |
|------|---------|---------|
| 8080 | Locker Server | REST API for locker control |
| 9091 | Web Monitor | Real-time monitoring interface |
| (SDK) | Robot | Fairino SDK communication |

### B. Error Codes

| Error | Description | Action |
|-------|-------------|--------|
| Connection Error | Cannot reach server/robot | Check network |
| Timeout Error | Operation took too long | Increase timeout |
| State Error | Unexpected locker state | Check hardware |
| Critical Error | Locker won't close | Physical inspection |

### C. Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging information |
| INFO | General informational messages |
| WARNING | Warning messages (non-critical) |
| ERROR | Error messages (cycle failures) |
| CRITICAL | Critical errors (require intervention) |

### D. Glossary

- **Cycle** - One complete operation: open→verify→robot→close
- **Phase** - A step within a cycle
- **State Verification** - Checking locker changed state
- **SDK Feedback** - Real-time position data from robot
- **Blocking Command** - Command that waits for completion
- **Session Cookie** - Authentication token for locker server

---

## 📊 Version History

### Version 2.0 (Current)
- ✅ Added statistics tracking
- ✅ Final summary on shutdown
- ✅ Web interface with live statistics
- ✅ Success/failure counters
- ✅ Enhanced logging

### Version 1.0
- Initial release
- Basic cycle management
- Locker and robot integration
- Web monitoring interface

---

## ✅ Checklist for First Run

Before running the system for the first time:

- [ ] Python 3.7+ installed
- [ ] Dependencies installed (`requests`, `fairino`)
- [ ] Network connectivity verified
- [ ] Can ping 72.61.181.1 (locker server)
- [ ] Can ping 192.168.58.101 (robot)
- [ ] Configuration reviewed in `main.py`
- [ ] Locker number set (TARGET_LOCKER)
- [ ] Tested individual components
- [ ] Understand safety features
- [ ] Read troubleshooting section

---

**🎉 You're ready to use the Locker-Robot Integration System!**

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or check the detailed logs in `cycle_controller.log`.

---

*Document End*
