#!/usr/bin/env python3
"""
Test Minecraft-specific input by finding and focusing the Minecraft window
"""

import subprocess
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minecraft_ai.automation.input_controller import create_input_controller

def focus_minecraft_window():
    """Use AppleScript to focus Minecraft window"""
    try:
        # Try to find and focus Minecraft window
        script = '''
        tell application "System Events"
            set minecraftApp to first application process whose name contains "Minecraft"
            set frontmost of minecraftApp to true
            return "Minecraft focused"
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Minecraft window focused")
            return True
        else:
            print("❌ Could not focus Minecraft window")
            print("Error:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error focusing Minecraft: {e}")
        return False

def test_minecraft_movement():
    print("🎮 Testing Minecraft-specific movement...")
    
    # First, try to focus Minecraft
    if not focus_minecraft_window():
        print("⚠️  Continuing anyway - manually click on Minecraft window now!")
        time.sleep(3)
    
    time.sleep(1)  # Give time for window focus
    
    controller = create_input_controller(dry_run=False)
    
    print("Testing movement keys...")
    
    # Test forward movement
    print("1. Moving forward (W)...")
    controller.key_press('w')
    time.sleep(0.5)
    controller.key_release('w')
    time.sleep(1)
    
    # Test other movements
    print("2. Moving left (A)...")
    controller.key_press('a')
    time.sleep(0.5)
    controller.key_release('a')
    time.sleep(1)
    
    print("3. Jump (Space)...")
    controller.key_press('space')
    time.sleep(0.1)
    controller.key_release('space')
    time.sleep(1)
    
    print("✅ Test complete!")
    print("Did you see movement in Minecraft this time?")

if __name__ == "__main__":
    test_minecraft_movement()