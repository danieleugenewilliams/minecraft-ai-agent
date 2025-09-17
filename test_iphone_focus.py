#!/usr/bin/env python3
"""
Test script to verify iPhone Mirroring focus and input
"""

import time
import subprocess
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minecraft_ai.automation.input_controller import MacOSInputController

def test_focus_and_input():
    """Test focusing iPhone Mirroring and sending simple input"""
    
    print("Testing iPhone Mirroring focus and input...")
    
    # Create input controller
    controller = MacOSInputController()
    
    # Test 1: Focus iPhone Mirroring
    print("\n1. Attempting to focus iPhone Mirroring...")
    success = controller.focus_minecraft_window()
    if success:
        print("✅ Successfully focused iPhone Mirroring")
    else:
        print("❌ Failed to focus iPhone Mirroring")
        return False
    
    # Test 2: Send a simple key press
    print("\n2. Testing key input (up arrow for 1 second)...")
    time.sleep(2)  # Give user time to see the focus
    
    controller.key_press('up')
    time.sleep(1)
    controller.key_release('up')
    print("✅ Sent up arrow key")
    
    # Test 3: Test looking around
    print("\n3. Testing look controls (j and l keys)...")
    time.sleep(1)
    
    controller.key_press('j')  # Look left
    time.sleep(0.5)
    controller.key_release('j')
    
    time.sleep(0.5)
    
    controller.key_press('l')  # Look right
    time.sleep(0.5)
    controller.key_release('l')
    print("✅ Sent look left/right keys")
    
    # Test 4: Center view
    print("\n4. Testing center view (enter key)...")
    time.sleep(1)
    controller.center_view()
    print("✅ Sent center view command")
    
    print("\n✅ All tests completed!")
    print("If you saw movement in Minecraft, the calibration is working!")
    return True

if __name__ == "__main__":
    test_focus_and_input()