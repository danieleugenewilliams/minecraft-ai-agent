#!/usr/bin/env python3
"""
Test forward movement specifically
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minecraft_ai.automation.input_controller import create_input_controller

def test_forward_movement():
    print("🎮 Testing forward movement...")
    print("Make sure Minecraft is focused!")
    print("Starting in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    controller = create_input_controller(dry_run=False)
    
    print("Moving forward for 2 seconds...")
    controller.key_press('w')
    time.sleep(2)
    controller.key_release('w')
    
    print("✅ Forward movement test complete!")
    print("Did your character move forward?")

if __name__ == "__main__":
    test_forward_movement()