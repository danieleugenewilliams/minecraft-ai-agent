#!/usr/bin/env python3
"""
Long-Range Water Search - Summary Version
Shows key milestones during the 100-200 step journey
"""

import requests
import mss
import numpy as np
from PIL import Image
import time
import argparse
import pyautogui
import subprocess
import sys
import os

def focus_minecraft_window():
    """Focus the iPhone Mirroring app where Minecraft is running"""
    try:
        script = '''tell application "iPhone Mirroring" to activate'''
        subprocess.run(['osascript', '-e', script], 
                     capture_output=True, text=True, timeout=3)
        time.sleep(0.2)
        return True
    except:
        return False

def capture_and_analyze_for_water():
    """Capture screen and analyze for water (optimized)"""
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Water detection - blue color ranges (RGB)
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Water color ranges
        water_colors = [
            [(30, 100, 150), (100, 180, 255)],     # Light blue water
            [(20, 60, 120), (80, 120, 200)],       # Deeper blue water
            [(60, 140, 180), (120, 200, 255)],     # Bright water surface
        ]
        
        total_water_coverage = 0
        for lower, upper in water_colors:
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            total_water_coverage += np.sum(mask) / total_pixels
        
        # Region analysis (6 regions)
        height, width = img_array.shape[:2]
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3],
            'right': img_array[:, 2*width//3:],
            'top': img_array[:height//3, :],
            'middle': img_array[height//3:2*height//3, :],
            'bottom': img_array[2*height//3:, :],
        }
        
        region_water = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            region_coverage = 0
            for lower, upper in water_colors:
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                region_coverage += np.sum(mask) / region_pixels
            region_water[region_name] = region_coverage
        
        return {
            'total_water_coverage': total_water_coverage,
            'region_water': region_water
        }
        
    except Exception as e:
        return None

def get_smart_command(coverage, regions, step_num, mission_phase):
    """Get navigation command for long-range water search - anti-spinning"""
    
    if mission_phase == "SEARCH":
        # Structured search pattern - avoid excessive spinning
        search_cycle = step_num % 24
        if search_cycle < 3:
            return 'j'  # Look left
        elif search_cycle < 6:
            return 'l'  # Look right
        elif search_cycle < 8:
            return 'i' if search_cycle == 6 else 'k'  # Look up/down
        elif search_cycle < 15:
            return 'w'  # Move forward
        elif search_cycle < 18:
            return 'a'  # Turn left
        else:
            return 'd'  # Turn right
        
    elif mission_phase == "NAVIGATE":
        # Decisive movement toward water
        max_region = max(regions['left'], regions['center'], regions['right'])
        
        if regions['left'] == max_region and regions['left'] > 0.01:
            if step_num % 8 < 2:
                return 'a'  # Turn toward water
            else:
                return 'w'  # Move forward
        elif regions['right'] == max_region and regions['right'] > 0.01:
            if step_num % 8 < 2:
                return 'd'  # Turn toward water
            else:
                return 'w'  # Move forward
        else:
            return 'w'  # Move forward
            
    else:  # APPROACH phase
        if coverage > 0.08:
            return 'w'  # Just move forward when close
        else:
            return 'w'

def determine_mission_phase(coverage, step_num, max_coverage_seen):
    """Determine current mission phase"""
    if coverage < 0.005 and max_coverage_seen < 0.01 and step_num < 80:
        return "SEARCH"
    elif coverage > 0.08 or max_coverage_seen > 0.08:
        return "APPROACH"
    else:
        return "NAVIGATE"

def execute_minecraft_command(command, duration=0.5):
    """Execute command in Minecraft"""
    focus_minecraft_window()
    pyautogui.keyDown(command)
    time.sleep(duration)
    pyautogui.keyUp(command)

def main():
    parser = argparse.ArgumentParser(description='Long-Range Water Search Mission')
    parser.add_argument('--ready', choices=['y', 'n'], default='n')
    parser.add_argument('--steps', type=int, default=200)
    args = parser.parse_args()
    
    print("💧🗺️ Long-Range Water Search Mission")
    print("=" * 50)
    
    if args.ready != 'y':
        print("❌ Use --ready y to start mission")
        return
    
    print(f"🚀 Starting {args.steps}-step mission...")
    print("Will show progress every 20 steps\n")
    time.sleep(2)
    
    # Mission tracking
    commands = []
    max_coverage = 0
    water_first_detected = None
    mission_phase = "SEARCH"
    last_significant_water = 0
    
    for step in range(args.steps):
        # Analyze
        visual_data = capture_and_analyze_for_water()
        if not visual_data:
            continue
        
        coverage = visual_data['total_water_coverage']
        regions = visual_data['region_water']
        max_coverage = max(max_coverage, coverage)
        
        # Update mission phase
        mission_phase = determine_mission_phase(coverage, step, max_coverage)
        
        # Track significant events
        if coverage > 0.01 and water_first_detected is None:
            water_first_detected = step
            print(f"🎯 WATER FIRST DETECTED at step {step + 1}! Coverage: {coverage:.3%}")
        
        if coverage > 0.05:
            last_significant_water = step
            print(f"🌊 SIGNIFICANT WATER at step {step + 1}! Coverage: {coverage:.3%}")
        
        # Progress reporting (every 20 steps)
        if step % 20 == 0 or coverage > 0.08:
            print(f"Step {step + 1:3d}: 💧{coverage:.3%} | {mission_phase:8s} | "
                  f"Max:{max_coverage:.3%} | L{regions['left']:.2%} C{regions['center']:.2%} R{regions['right']:.2%}")
        
        # Check mission success
        if coverage > 0.15:
            print(f"\n🏆 MISSION SUCCESS at step {step + 1}!")
            print(f"   Within 5 steps of large water body! Coverage: {coverage:.3%}")
            break
        elif coverage > 0.12:
            print(f"🎉 VERY CLOSE TO WATER at step {step + 1}! Coverage: {coverage:.3%}")
        
        # Get and execute command
        command = get_smart_command(coverage, regions, step, mission_phase)
        commands.append(command)
        
        execute_minecraft_command(command, duration=0.4)
        time.sleep(0.2)  # Fast execution
    
    # Mission Results
    print(f"\n🏁 Long-Range Water Search Complete!")
    print("=" * 50)
    print(f"📊 Mission Statistics:")
    print(f"   Total steps: {len(commands)}")
    print(f"   Max water coverage: {max_coverage:.3%}")
    print(f"   Water first detected: {'Step ' + str(water_first_detected + 1) if water_first_detected else 'Never'}")
    print(f"   Last significant water: {'Step ' + str(last_significant_water + 1) if last_significant_water else 'Never'}")
    print(f"   Final phase: {mission_phase}")
    
    if max_coverage > 0.15:
        print(f"\n🎉 MISSION SUCCESS: Reached large water body!")
        if water_first_detected:
            travel_distance = len(commands) - water_first_detected
            print(f"   Traveled {travel_distance} steps from first detection to arrival")
    elif max_coverage > 0.08:
        print(f"\n✅ Partial Success: Found significant water ({max_coverage:.3%})")
    elif water_first_detected:
        print(f"\n⚠️ Water detected but mission incomplete")
    else:
        print(f"\n❌ No water detected - try different starting position")

if __name__ == "__main__":
    main()