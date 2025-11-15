#!/usr/bin/env python3
"""
Smart Locker Client - Control from Laptop
Connects to Server: 72.61.181.1:8080
"""

import requests
import json
from typing import Dict, Optional, List

class LockerClient:
    """Client for remote locker system control"""
    
    def __init__(self, server_ip: str = "72.61.181.1", port: int = 8080, password: str = "Cyber@Abed1102"):
        """
        Args:
            server_ip: Server address
            port: Connection port
            password: Authentication password
        """
        self.base_url = f"http://{server_ip}"
        self.password = password
        self.session_cookie = None
        self._login()
    
    def _login(self) -> bool:
        """Login and obtain session"""
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json={"password": self.password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.session_cookie = data.get('session')
                    print(f"✅ Connected to server: {self.base_url}")
                    return True
            
            print(f"❌ Login failed: {response.status_code}")
            return False
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server: {self.base_url}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with session cookie"""
        return {
            "Cookie": f"session={self.session_cookie}",
            "Content-Type": "application/json"
        }
    
    def open_locker(self, locker_num: int) -> Dict:
        """
        Open specific locker
        
        Args:
            locker_num: Locker number (1-12)
            
        Returns:
            dict: Operation result
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/locker/{locker_num}/open",
                headers=self._get_headers(),
                timeout=5
            )
            
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Locker {locker_num} opened")
            else:
                print(f"❌ Failed to open locker {locker_num}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error opening locker {locker_num}: {e}")
            return {'success': False, 'error': str(e)}
    
    def open_multiple_lockers(self, locker_numbers: List[int], delay: float = 0.5) -> List[Dict]:
        """
        Open multiple lockers
        
        Args:
            locker_numbers: List of locker numbers
            delay: Delay between each locker (seconds)
            
        Returns:
            list: Results of all operations
        """
        import time
        results = []
        
        for locker_num in locker_numbers:
            result = self.open_locker(locker_num)
            results.append(result)
            if delay > 0:
                time.sleep(delay)
        
        return results
    
    def open_all_lockers(self, delay: float = 0.4) -> List[Dict]:
        """Open all lockers (1-12)"""
        print("🔓 Opening all lockers...")
        return self.open_multiple_lockers(range(1, 13), delay)
    
    def get_status(self) -> Optional[Dict]:
        """
        Get system status
        
        Returns:
            dict: System status and all lockers
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/status",
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return None
    
    def get_locker_status(self, locker_num: int) -> Optional[Dict]:
        """Get specific locker status"""
        status = self.get_status()
        if status and 'lockers' in status:
            return status['lockers'].get(str(locker_num))
        return None
    
    def is_locker_open(self, locker_num: int) -> bool:
        """Check door status (open/closed)"""
        locker = self.get_locker_status(locker_num)
        if locker:
            return locker.get('door_open', False)
        return False
    
    def is_locker_empty(self, locker_num: int) -> bool:
        """Check sensor status (empty/occupied)"""
        locker = self.get_locker_status(locker_num)
        if locker:
            return locker.get('sensor_status') == 'Empty'
        return False
    
    def print_status(self):
        """Print system status in organized format"""
        status = self.get_status()
        if not status:
            print("❌ Cannot get status")
            return
        
        print("\n" + "="*60)
        print("📊 Smart Locker System Status")
        print("="*60)
        print(f"🔗 Connection: {'🟢 Connected' if status.get('connected') else '🔴 Disconnected'}")
        print(f"⏱️  Uptime: {status.get('uptime')}s")
        print(f"📤 Total Commands: {status.get('total_commands')}")
        print("\n" + "-"*60)
        print("Lockers:")
        print("-"*60)
        
        lockers = status.get('lockers', {})
        for locker_id in sorted(lockers.keys(), key=int):
            locker = lockers[locker_id]
            door = "🔓 Open" if locker['door_open'] else "🔒 Closed"
            sensor_icons = {'Empty': '✅ Empty', 'Occupied': '🚫 Occupied', 'Unknown': '❓ Unknown'}
            sensor = sensor_icons.get(locker['sensor_status'], '❓')
            print(f"  Locker {locker_id:2s}: {door:10s} | {sensor}")
        
        print("="*60 + "\n")
    
    def wait_for_locker_close(self, locker_num: int, timeout: int = 30) -> bool:
        """
        Wait until locker closes
        
        Args:
            locker_num: Locker number
            timeout: Maximum wait time (seconds)
            
        Returns:
            bool: True if closed, False if timeout
        """
        import time
        start_time = time.time()
        
        print(f"⏳ Waiting for locker {locker_num} to close...")
        
        while (time.time() - start_time) < timeout:
            if not self.is_locker_open(locker_num):
                print(f"✅ Locker {locker_num} closed")
                return True
            time.sleep(1)
        
        print(f"⏰ Timeout waiting for locker {locker_num}")
        return False
    
    # ============================================
    # NEW SIMPLE DIRECT FUNCTIONS
    # ============================================
    
    def openLocker(self, locker_num: int) -> bool:
        """
        Simple direct function to open locker (for use in other code)
        
        Args:
            locker_num: Locker number (1-12)
            
        Returns:
            bool: True if opened successfully, False otherwise
        
        Example:
            client.openLocker(2)  # Opens locker 2
        """
        result = self.open_locker(locker_num)
        return result.get('success', False)
    
    def lockerStatus(self, locker_num: int) -> str:
        """
        Simple function to check if locker door is open or closed
        
        Args:
            locker_num: Locker number (1-12)
            
        Returns:
            str: "Open", "Closed", or "Unknown"
        
        Example:
            status = client.lockerStatus(2)
            if status == "Open":
                print("Door is open!")
        """
        locker = self.get_locker_status(locker_num)
        if locker is None:
            return "Unknown"
        
        return "Open" if locker.get('door_open', False) else "Closed"
    
    def sensorStatus(self, locker_num: int) -> str:
        """
        Simple function to check if locker is empty or occupied (IR sensor)
        
        Args:
            locker_num: Locker number (1-12)
            
        Returns:
            str: "Empty", "Occupied", or "Unknown"
        
        Example:
            sensor = client.sensorStatus(2)
            if sensor == "Empty":
                print("Locker is empty!")
        """
        locker = self.get_locker_status(locker_num)
        if locker is None:
            return "Unknown"
        
        return locker.get('sensor_status', 'Unknown')


# ============================================
# SIMPLE USAGE EXAMPLES
# ============================================

def simple_example():
    """Simple example using new functions"""
    print("\n🔹 Simple Example - New Functions\n")
    
    # Connect to server
    client = LockerClient()
    
    # Use simple functions
    locker_num = 2
    
    # 1. Open locker directly
    print(f"\n1. Opening locker {locker_num}...")
    if client.openLocker(locker_num):
        print(f"   ✅ Success!")
    else:
        print(f"   ❌ Failed!")
    
    # 2. Check door status
    print(f"\n2. Checking door status...")
    door_status = client.lockerStatus(locker_num)
    print(f"   Door is: {door_status}")
    
    # 3. Check sensor status
    print(f"\n3. Checking sensor status...")
    sensor = client.sensorStatus(locker_num)
    print(f"   Sensor reads: {sensor}")
    
    print("\n" + "="*60)


def integration_example():
    """Example: Using in another code"""
    print("\n🔹 Integration Example\n")
    
    client = LockerClient()
    
    # Check all lockers and open empty ones
    for i in range(1, 13):
        door = client.lockerStatus(i)
        sensor = client.sensorStatus(i)
        
        print(f"Locker {i}: Door={door}, Sensor={sensor}")
        
        if door == "Closed" and sensor == "Empty":
            print(f"  → Opening locker {i}...")
            client.openLocker(i)


# ============================================
# OLD EXAMPLES (kept for compatibility)
# ============================================

def example_basic_usage():
    """Example 1: Basic usage"""
    print("\n🔹 Example 1: Basic Usage\n")
    
    # Connect to server
    client = LockerClient()
    
    # Open single locker
    client.open_locker(5)
    
    # Get status
    client.print_status()


def example_multiple_lockers():
    """Example 2: Open multiple lockers"""
    print("\n🔹 Example 2: Open Multiple Lockers\n")
    
    client = LockerClient()
    
    # Open specific lockers
    lockers_to_open = [1, 3, 5, 7]
    client.open_multiple_lockers(lockers_to_open)


def example_check_and_open():
    """Example 3: Check before opening"""
    print("\n🔹 Example 3: Open Empty Lockers Only\n")
    
    client = LockerClient()
    
    # Open empty lockers only
    for locker_num in range(1, 13):
        if client.is_locker_empty(locker_num):
            print(f"Locker {locker_num} is empty - opening")
            client.open_locker(locker_num)
        else:
            print(f"Locker {locker_num} is occupied - skipping")


def example_integration_with_other_code():
    """Example 4: Integration with other code"""
    print("\n🔹 Example 4: Integration with Other Code\n")
    
    client = LockerClient()
    
    # Example: Simple booking system
    bookings = {
        "Ahmed": 3,
        "Sara": 7,
        "Omar": 12
    }
    
    for name, locker_num in bookings.items():
        print(f"📦 Booking for {name} - opening locker {locker_num}")
        client.open_locker(locker_num)
        client.wait_for_locker_close(locker_num, timeout=10)


# ============================================
# Direct Execution
# ============================================

#if __name__ == "__main__":
    # Test new simple functions
  #  simple_example()
    
    # Or use old examples
    # example_basic_usage()
    
    # Or interactive usage
    # client = LockerClient()
    # client.openLocker(2)
    # print(client.lockerStatus(2))
    # print(client.sensorStatus(2)) 