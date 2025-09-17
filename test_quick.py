#!/usr/bin/env python3
"""Quick test"""
import subprocess
import time

def focus_minecraft():
    try:
        subprocess.run(['osascript', '-e', 'tell application "iPhone Mirroring" to activate'], 
                     capture_output=True, text=True, timeout=3)
        return True
    except:
        return False

print("Testing focus...")
result = focus_minecraft()
print(f"Focus result: {result}")
time.sleep(1)
print("Done")