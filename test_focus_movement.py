#!/usr/bin/env python3
"""
Test movement with window focus
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minecraft_ai.automation.input_controller import create_input_controller

def test_movement_with_focus():
    print("🎮 Testing movement with window focus...")
    print("Position your Minecraft window where you can see it")
    print("Starting in 5 seconds...")
    
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    controller = create_input_controller(dry_run=False)
    
    # First, click in the center of screen to focus Minecraft
    print("1. Clicking to focus Minecraft window...")
    controller.click(500, 400, 'left')
    time.sleep(1)
    
    # Test key sequence
    print("2. Testing W key (forward)...")
    controller.key_press('w')
    time.sleep(1)
    controller.key_release('w')
    time.sleep(1)
    
    print("3. Testing A key (left)...")
    controller.key_press('a')
    time.sleep(1) 
    controller.key_release('a')
    time.sleep(1)
    
    print("4. Testing S key (back)...")
    controller.key_press('s')
    time.sleep(1)
    controller.key_release('s')
    time.sleep(1)
    
    print("5. Testing D key (right)...")
    controller.key_press('d')
    time.sleep(1)
    controller.key_release('d')
    
    print("✅ Movement test complete!")
    print("Did you see any movement in Minecraft?")

if __name__ == "__main__":
    test_movement_with_focus()