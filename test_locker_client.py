#!/usr/bin/env python3
"""
Example: How to use the new simple functions in locker_client.py
"""

from locker_client import LockerClient

# ============================================
# EXAMPLE 1: Basic Usage
# ============================================

def example_1_basic():
    """Simple basic usage"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)
    
    # Create client (auto-connects)
    client = LockerClient()
    
    # Open locker 2
    client.openLocker(1)
    
    # Check door status
    door = client.lockerStatus(1)
    print(f"Door is: {door}")
    
    # Check sensor
    sensor = client.sensorStatus(1)
    print(f"Sensor reads: {sensor}")


# ============================================
# RUN EXAMPLE
# ============================================

if __name__ == "__main__":
    # Run all examples
    
    example_1_basic()
    
    # Uncomment to run other examples:
    # example_2_integration()
    # example_3_loop()
    # example_4_conditional()
    
    # Or test custom function:
    # my_open_and_wait(2) 

