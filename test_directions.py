#!/usr/bin/env python3
"""
Test individual directional controls
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minecraft_ai.automation.input_controller import create_input_controller

def test_all_directions():
    print("🎮 Testing all directional controls...")
    print("Make sure Minecraft is focused!")
    print("Starting in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    controller = create_input_controller(dry_run=False)
    
    # Test each direction
    directions = [
        ('up', 'UP arrow'),
        ('down', 'DOWN arrow'), 
        ('left', 'LEFT arrow'),
        ('right', 'RIGHT arrow')
    ]
    
    for key, name in directions:
        print(f"Testing {name} key...")
        controller.key_press(key)
        time.sleep(1)
        controller.key_release(key)
        time.sleep(1)
        print(f"Did you see movement for {name}?")
        input("Press Enter to continue...")

if __name__ == "__main__":
    test_all_directions()