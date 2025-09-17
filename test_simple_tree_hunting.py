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

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def focus_minecraft_window():
    """Focus the iPhone Mirroring app where Minecraft is running"""
    try:
        # Try iPhone Mirroring app first (where Minecraft is likely running)
        minecraft_names = ["iPhone Mirroring", "Minecraft", "minecraft", "MinecraftLauncher"]
        
        for name in minecraft_names:
            script = f'''
            tell application "System Events"
                try
                    set targetApp to first application process whose name is "{name}"
                    set frontmost of targetApp to true
                    return "focused"
                on error
                    return "not found"
                end try
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "focused" in result.stdout:
                print(f"✅ Successfully focused: {name}")
                time.sleep(0.5)  # Give time for focus to take effect
                return True
        
        # Fallback: try to click on iPhone Mirroring window if it exists
        script = '''
        tell application "iPhone Mirroring" to activate
        '''
        try:
            subprocess.run(['osascript', '-e', script], 
                         capture_output=True, text=True, timeout=3)
            time.sleep(0.5)
            print("✅ Activated iPhone Mirroring app")
            return True
        except:
            pass
        
        print("⚠️ Could not focus Minecraft window")
        return False
    except Exception as e:
        print(f"❌ Error focusing window: {e}")
        return False

def capture_and_analyze_for_water():
    """Capture screen and analyze for water"""
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Save with timestamp
        timestamp = int(time.time())
        filename = f"water_hunt_{timestamp}.png"
        img.save(filename)
        
        # Water detection - blue color ranges (RGB)
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Water color ranges - various shades of blue/cyan
        water_colors = {
            'water_blue': [(30, 100, 150), (100, 180, 255)],     # Light blue water
            'deep_water': [(20, 60, 120), (80, 120, 200)],       # Deeper blue water
            'water_surface': [(60, 140, 180), (120, 200, 255)],  # Bright water surface
        }
        
        total_water_coverage = 0
        for color_name, (lower, upper) in water_colors.items():
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            coverage = np.sum(mask) / total_pixels
            total_water_coverage += coverage
        
        # Region analysis
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
            for color_name, (lower, upper) in water_colors.items():
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                region_coverage += np.sum(mask) / region_pixels
            region_water[region_name] = region_coverage
        
        return {
            'total_water_coverage': total_water_coverage,
            'region_water': region_water,
            'filename': filename
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def get_smart_command(visual_data, step_num, mission_phase):
    """Get navigation command from LLM for long-range water search"""
    
    coverage = visual_data['total_water_coverage']
    regions = visual_data['region_water']
    
    system_prompt = f"""You are a Minecraft AI on a LONG-RANGE water search mission. Phase: {mission_phase}

Commands:
- w/a/s/d: move forward/left/backward/right  
- i/k/j/l: look up/down/left/right

Mission Strategy:
PHASE 1 (SEARCH): Turn around completely to spot distant water
- Use camera controls to look in ALL directions (360° search)
- Look for ANY water in distance (even tiny amounts)
- Priority: j/l (horizontal scanning), then i/k (vertical)

PHASE 2 (NAVIGATE): Move toward detected water consistently  
- Use movement commands to travel toward water direction
- Occasional camera adjustments to maintain heading
- Keep moving forward (w) toward water region

PHASE 3 (APPROACH): Get within 5 steps of large water body
- Fine-tune approach with movement commands
- Look for high water coverage (>8%)

Current phase guidance: {mission_phase}
Respond with ONE letter only."""

    user_prompt = f"""Water Mission Status:
Total coverage: {coverage:.3%}
Horizontal - Left: {regions['left']:.2%}, Center: {regions['center']:.2%}, Right: {regions['right']:.2%}
Vertical - Top: {regions['top']:.2%}, Middle: {regions['middle']:.2%}, Bottom: {regions['bottom']:.2%}
Step: {step_num} | Phase: {mission_phase}

What command?"""

    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "").strip().lower()
            
            # Extract command
            valid_commands = ['w', 's', 'a', 'd', 'i', 'k', 'j', 'l']
            for cmd in valid_commands:
                if cmd in llm_response:
                    return cmd
        
        # Enhanced fallback logic based on mission phase
        if mission_phase == "SEARCH":
            # Systematic 360° camera scanning
            scan_pattern = ['j', 'j', 'l', 'l', 'l', 'l', 'i', 'k']  # Look left, right, up, down
            return scan_pattern[step_num % len(scan_pattern)]
            
        elif mission_phase == "NAVIGATE":
            # Determine best direction and move toward it
            if regions['left'] > max(regions['center'], regions['right']):
                if step_num % 4 == 0:
                    return 'j'  # Occasional left look
                return 'a'  # Move left
            elif regions['right'] > max(regions['center'], regions['left']):
                if step_num % 4 == 0:
                    return 'l'  # Occasional right look  
                return 'd'  # Move right
            else:
                return 'w'  # Move forward toward center
                
        else:  # APPROACH phase
            if regions['bottom'] > regions['middle']:
                return 'k'  # Look down at nearby water
            elif coverage > 0.05:
                return 'w'  # Move toward water
            else:
                return 'w'  # Keep moving forward
            
    except Exception as e:
        print(f"⚠️ LLM failed: {e}")
        # Cycle through all controls when LLM fails
        all_commands = ['w', 'a', 's', 'd', 'j', 'l', 'i', 'k']
        return all_commands[step_num % len(all_commands)]

def determine_mission_phase(coverage, step_num, max_coverage_seen):
    """Determine current mission phase based on water detection"""
    if coverage < 0.01 and max_coverage_seen < 0.02 and step_num < 50:
        return "SEARCH"  # Still looking for water
    elif coverage > 0.08 or max_coverage_seen > 0.08:
        return "APPROACH"  # Close to significant water  
    else:
        return "NAVIGATE"  # Found water, moving toward it

def execute_minecraft_command(command, duration=1.0):
    """Execute command in Minecraft with proper window focusing"""
    print(f"🎮 Executing: {command} for {duration}s")
    
    try:
        # Focus the iPhone Mirroring window first
        if not focus_minecraft_window():
            print("⚠️ Warning: Could not confirm window focus - trying anyway")
        
        # Execute command
        pyautogui.keyDown(command)
        time.sleep(duration)
        pyautogui.keyUp(command)
        
        print(f"✅ Executed: {command}")
        return True
        
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Long-Range Water Search Mission')
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Start water search mission')
    parser.add_argument('--steps', type=int, default=250,
                       help='Number of steps (default 250 for long mission)')
    args = parser.parse_args()
    
    print("💧🗺️ Long-Range Water Search Mission")
    print("=" * 50)
    print("Mission: Find distant water and navigate 100-200 steps to reach it")
    
    if args.ready != 'y':
        print("❌ Use --ready y to start mission")
        return
    
    print(f"🚀 Starting {args.steps}-step mission in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Mission tracking
    commands = []
    max_coverage = 0
    found_water = False
    water_first_detected = None
    mission_phase = "SEARCH"
    
    for step in range(args.steps):
        print(f"\n🔄 Step {step + 1}/{args.steps}")
        
        # Analyze
        visual_data = capture_and_analyze_for_water()
        if not visual_data:
            continue
        
        coverage = visual_data['total_water_coverage']
        max_coverage = max(max_coverage, coverage)
        
        # Update mission phase
        mission_phase = determine_mission_phase(coverage, step, max_coverage)
        
        # Track when water is first detected
        if coverage > 0.01 and water_first_detected is None:
            water_first_detected = step
            print(f"🎯 WATER DETECTED at step {step + 1}!")
        
        regions = visual_data['region_water']
        print(f"💧 Water: {coverage:.3%} | Phase: {mission_phase}")
        print(f"   H: L{regions['left']:.2%} C{regions['center']:.2%} R{regions['right']:.2%}")
        print(f"   V: T{regions['top']:.2%} M{regions['middle']:.2%} B{regions['bottom']:.2%}")
        
        # Check mission progress
        if coverage > 0.08:  # Significant water detected
            print("🎉 FOUND SIGNIFICANT WATER BODY!")
            found_water = True
            if coverage > 0.15:  # Very close - mission success
                print("🏆 MISSION SUCCESS: Within 5 steps of large water body!")
                break
        
        # Progress indicators
        if mission_phase == "SEARCH" and step % 20 == 0:
            print(f"🔍 Still searching... ({step} steps completed)")
        elif mission_phase == "NAVIGATE" and water_first_detected:
            steps_since_detection = step - water_first_detected
            print(f"🧭 Navigating toward water... ({steps_since_detection} steps since detection)")
        
        # Get and execute command
        command = get_smart_command(visual_data, step, mission_phase)
        commands.append(command)
        
        execute_minecraft_command(command, duration=0.8)  # Faster for long mission
        time.sleep(0.5)  # Shorter delay for efficiency
    
    # Mission Results
    print(f"\n🏁 Mission Complete!")
    print(f"Total steps: {len(commands)}")
    print(f"Commands executed: {' → '.join(commands[-20:])}")  # Show last 20 commands
    print(f"Max water coverage: {max_coverage:.3%}")
    print(f"Water first detected: {'Step ' + str(water_first_detected + 1) if water_first_detected else 'Never'}")
    print(f"Final phase: {mission_phase}")
    
    if found_water and max_coverage > 0.15:
        print("🎉 MISSION SUCCESS: Reached large water body!")
    elif found_water:
        print("✅ Partial Success: Found water but didn't get close enough")
        if water_first_detected:
            travel_distance = len(commands) - water_first_detected
            print(f"   Traveled {travel_distance} steps toward water")
    elif water_first_detected:
        print("⚠️ Water detected but lost during navigation")
    else:
        print("❌ No water detected - may need longer search or different starting position")

if __name__ == "__main__":
    main()