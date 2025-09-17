#!/usr/bin/env python3
"""
Live Minecraft test - actual input controls
WARNING: This will send real keyboard/mouse input!
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minecraft_ai.automation.input_controller import create_input_controller

def test_live_controls():
    """Test real input controls - USE WITH CAUTION"""
    print("⚠️  LIVE CONTROL TEST")
    print("This will send REAL keyboard input to your system!")
    print("Make sure Minecraft is focused and ready.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Test cancelled.")
        return
    
    print("Starting live control test in 3 seconds...")
    print("Move your mouse to Minecraft window now!")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("🎮 Starting live control test!")
    
    try:
        controller = create_input_controller(dry_run=False)
        
        # Test sequence
        print("1. Small forward movement...")
        controller.key_press('w')
        time.sleep(0.5)
        controller.key_release('w')
        time.sleep(1)
        
        print("2. Small backward movement...")
        controller.key_press('s')
        time.sleep(0.5)
        controller.key_release('s')
        time.sleep(1)
        
        print("3. Left turn...")
        controller.key_press('a')
        time.sleep(0.3)
        controller.key_release('a')
        time.sleep(1)
        
        print("4. Right turn...")
        controller.key_press('d')
        time.sleep(0.3)
        controller.key_release('d')
        time.sleep(1)
        
        print("5. Jump...")
        controller.key_press('space')
        time.sleep(0.1)
        controller.key_release('space')
        
        print("✅ Live control test completed!")
        print("Did you see the character move in Minecraft?")
        
    except Exception as e:
        print(f"❌ Live control test failed: {e}")

if __name__ == "__main__":
    test_live_controls()