#!/usr/bin/env python3
"""
Long-Range Water Search Mission
Agent searches for distant water bodies and navigates 100-200 steps to reach them
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
        script = '''
        tell application "iPhone Mirroring" to activate
        '''
        subprocess.run(['osascript', '-e', script], 
                     capture_output=True, text=True, timeout=3)
        time.sleep(0.3)
        return True
    except:
        return False

def capture_and_analyze_for_water():
    """Capture screen and analyze for water (optimized)"""
    try:
        print("📷 Capturing screenshot...")
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        print("🔍 Analyzing for water...")
        # Water detection - blue color ranges (RGB)
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Water color ranges - various shades of blue/cyan
        water_colors = [
            [(30, 100, 150), (100, 180, 255)],     # Light blue water
            [(20, 60, 120), (80, 120, 200)],       # Deeper blue water
            [(60, 140, 180), (120, 200, 255)],     # Bright water surface
        ]
        
        total_water_coverage = 0
        for lower, upper in water_colors:
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            total_water_coverage += np.sum(mask) / total_pixels
        
        print(f"💧 Water coverage: {total_water_coverage:.3%}")
        
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
        
        print("✅ Analysis complete")
        return {
            'total_water_coverage': total_water_coverage,
            'region_water': region_water
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def get_smart_command(coverage, regions, step_num, mission_phase):
    """Get navigation command for long-range water search - avoid spinning"""
    
    if mission_phase == "SEARCH":
        # More structured search pattern - avoid excessive spinning
        search_cycle = step_num % 20
        if search_cycle < 4:
            # Look left systematically
            return 'j'
        elif search_cycle < 8:
            # Look right systematically  
            return 'l'
        elif search_cycle < 10:
            # Look up/down briefly
            return 'i' if search_cycle == 8 else 'k'
        elif search_cycle < 15:
            # Move forward to new position
            return 'w'
        else:
            # Turn body (not just camera) to new direction
            return 'a' if search_cycle < 17 else 'd'
        
    elif mission_phase == "NAVIGATE":
        # Decisive movement toward water - minimal camera adjustment
        max_region = max(regions['left'], regions['center'], regions['right'])
        
        if regions['left'] == max_region and regions['left'] > 0.01:
            # Water on left - turn body left and move forward
            if step_num % 6 < 2:
                return 'a'  # Turn left
            else:
                return 'w'  # Move forward
        elif regions['right'] == max_region and regions['right'] > 0.01:
            # Water on right - turn body right and move forward
            if step_num % 6 < 2:
                return 'd'  # Turn right
            else:
                return 'w'  # Move forward
        else:
            # Water in center or move forward
            return 'w'
            
    else:  # APPROACH phase
        if coverage > 0.08:
            # Close to water - just move forward
            return 'w'
        elif regions['bottom'] > regions['middle'] * 1.5:
            # Water below - look down briefly then move
            if step_num % 4 == 0:
                return 'k'
            return 'w'
        else:
            return 'w'

def determine_mission_phase(coverage, step_num, max_coverage_seen):
    """Determine current mission phase based on water detection"""
    if coverage < 0.005 and max_coverage_seen < 0.01 and step_num < 80:
        return "SEARCH"  # Extended search phase
    elif coverage > 0.08 or max_coverage_seen > 0.08:
        return "APPROACH"  # Close to significant water  
    else:
        return "NAVIGATE"  # Found water, moving toward it

def execute_minecraft_command(command, duration=0.6):
    """Execute command in Minecraft with optimized timing"""
    focus_minecraft_window()
    pyautogui.keyDown(command)
    time.sleep(duration)
    pyautogui.keyUp(command)

def main():
    parser = argparse.ArgumentParser(description='Long-Range Water Search Mission')
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Start water search mission')
    parser.add_argument('--steps', type=int, default=150,
                       help='Number of steps (default 150)')
    args = parser.parse_args()
    
    print("💧🗺️ Long-Range Water Search Mission")
    print("=" * 50)
    
    if args.ready != 'y':
        print("❌ Use --ready y to start mission")
        return
    
    print(f"🚀 Starting {args.steps}-step mission in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("🎯 Mission starting...")
    
    # Mission tracking
    commands = []
    max_coverage = 0
    water_first_detected = None
    mission_phase = "SEARCH"
    
    for step in range(args.steps):
        print(f"\n🔄 Step {step + 1}/{args.steps} - Starting analysis...")
        
        # Analyze
        visual_data = capture_and_analyze_for_water()
        if not visual_data:
            print("⚠️ No visual data, continuing...")
            continue
        
        coverage = visual_data['total_water_coverage']
        regions = visual_data['region_water']
        max_coverage = max(max_coverage, coverage)
        
        print(f"📊 Coverage: {coverage:.3%}, Max: {max_coverage:.3%}")
        
        # Update mission phase
        mission_phase = determine_mission_phase(coverage, step, max_coverage)
        
        # Track when water is first detected
        if coverage > 0.01 and water_first_detected is None:
            water_first_detected = step
            print(f"🎯 WATER DETECTED at step {step + 1}!")
        
        # Progress reporting (every 10 steps)
        if step % 10 == 0:
            print(f"Step {step + 1}: 💧{coverage:.3%} | {mission_phase} | "
                  f"L{regions['left']:.2%} C{regions['center']:.2%} R{regions['right']:.2%}")
        
        # Check mission success
        if coverage > 0.15:
            print(f"🏆 MISSION SUCCESS at step {step + 1}! Within 5 steps of large water body!")
            break
        elif coverage > 0.08:
            print(f"🎉 SIGNIFICANT WATER FOUND at step {step + 1}!")
        
        # Get and execute command
        print(f"🎮 Getting command for phase: {mission_phase}")
        command = get_smart_command(coverage, regions, step, mission_phase)
        commands.append(command)
        
        print(f"🎮 Executing command: {command}")
        execute_minecraft_command(command, duration=0.6)
        time.sleep(0.3)  # Fast execution for long mission
        print(f"✅ Command {command} completed")
    
    # Mission Results
    print(f"\n🏁 Mission Complete!")
    print(f"Total steps: {len(commands)}")
    print(f"Max water coverage: {max_coverage:.3%}")
    print(f"Water first detected: {'Step ' + str(water_first_detected + 1) if water_first_detected else 'Never'}")
    print(f"Final phase: {mission_phase}")
    
    if max_coverage > 0.15:
        print("🎉 MISSION SUCCESS: Reached large water body!")
    elif max_coverage > 0.08:
        print("✅ Partial Success: Found significant water")
    elif water_first_detected:
        print("⚠️ Water detected but navigation incomplete")
    else:
        print("❌ No water detected - continue search from new position")

if __name__ == "__main__":
    main()