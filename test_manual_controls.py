#!/usr/bin/env python3
"""
Manual test to verify Minecraft controls are working
"""

import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minecraft_ai.automation.input_controller import MacOSInputController

def manual_movement_test():
    """Test each movement key individually with user confirmation"""
    
    print("=== Minecraft Manual Movement Test ===")
    print("Make sure Minecraft is visible on screen!")
    print("")
    
    controller = MacOSInputController()
    
    # Focus first
    print("1. Focusing iPhone Mirroring...")
    success = controller.focus_minecraft_window()
    if success:
        print("✅ Successfully focused iPhone Mirroring")
    else:
        print("❌ Failed to focus - check if iPhone Mirroring is running")
        return
    
    time.sleep(2)
    
    # Test each key with user confirmation
    tests = [
        ("Forward movement", "up", 1.0),
        ("Look left", "j", 0.5),
        ("Look right", "l", 0.5), 
        ("Look down", "k", 0.5),
        ("Look up", "i", 0.5),
        ("Center view", "enter", 0.1),
        ("Left click (mine)", "click", 0.1)
    ]
    
    for i, (description, key, duration) in enumerate(tests, 2):
        print(f"\n{i}. Testing: {description}")
        print(f"   Pressing '{key}' for {duration} seconds...")
        print("   Watch Minecraft screen for movement!")
        
        time.sleep(1)  # Give user time to watch
        
        if key == "click":
            # Test clicking
            current_pos = controller.get_mouse_position()
            controller.click(current_pos[0], current_pos[1], 'left')
        else:
            # Test key press
            controller.key_press(key)
            time.sleep(duration)
            controller.key_release(key)
        
        # Ask user if they saw movement
        response = input(f"   Did you see movement/action in Minecraft? (y/n): ").lower().strip()
        if response == 'y':
            print(f"   ✅ {description} working!")
        else:
            print(f"   ❌ {description} not working!")
            
        time.sleep(0.5)
    
    print("\n=== Test Complete ===")
    print("If some controls aren't working, we need to adjust the key mappings.")

if __name__ == "__main__":
    manual_movement_test()