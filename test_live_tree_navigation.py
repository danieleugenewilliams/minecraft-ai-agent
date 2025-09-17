#!/usr/bin/env python3
"""
LIVE Tree Navigation Test
Actually moves the character toward trees using vision + controls
"""

import requests
import mss
import numpy as np
from PIL import Image
import json
import time
import pyautogui
import argparse

def capture_and_analyze_for_trees():
    """Capture screen and perform tree-specific analysis"""
    print("📸 Capturing screen for tree detection...")
    
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Save for verification
        img.save("live_tree_navigation.png")
        print(f"✅ Screenshot saved ({img.size[0]}x{img.size[1]})")
        
        # Tree-focused color analysis
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Tree color ranges (RGB)
        tree_color_ranges = {
            'wood_trunk': [(80, 40, 20), (160, 100, 70)],
            'green_leaves': [(20, 60, 20), (100, 180, 100)],
            'dark_leaves': [(10, 40, 10), (60, 120, 60)],
        }
        
        print("\n🌳 Tree Analysis:")
        tree_results = {}
        
        for color_name, (lower, upper) in tree_color_ranges.items():
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            coverage = np.sum(mask) / total_pixels
            tree_results[color_name] = coverage
            print(f"  {color_name:12}: {coverage:7.2%}")
        
        # Calculate total tree coverage
        total_tree_coverage = sum(tree_results.values())
        
        # Screen region analysis for navigation
        height, width = img_array.shape[:2]
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3],
            'right': img_array[:, 2*width//3:],
        }
        
        region_tree_coverage = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            region_trees = 0
            
            for color_name, (lower, upper) in tree_color_ranges.items():
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                region_trees += np.sum(mask) / region_pixels
            
            region_tree_coverage[region_name] = region_trees
        
        print(f"🎯 Total tree coverage: {total_tree_coverage:.2%}")
        for region, coverage in region_tree_coverage.items():
            print(f"   {region}: {coverage:.2%}")
        
        return {
            'total_tree_coverage': total_tree_coverage,
            'region_analysis': region_tree_coverage,
            'tree_results': tree_results
        }
        
    except Exception as e:
        print(f"❌ Tree analysis failed: {e}")
        return None

def get_navigation_command(visual_data):
    """Get navigation command from LLM"""
    print("🧠 Getting navigation command...")
    
    system_prompt = """You are a Minecraft movement AI. Analyze tree data and respond with a single movement command.

Commands: "w" (forward), "a" (left), "s" (backward), "d" (right), "stop"

Respond with ONLY the command, no explanation."""

    user_prompt = f"""Tree coverage detected:
- Total: {visual_data['total_tree_coverage']:.2%}
- Left: {visual_data['region_analysis']['left']:.2%}
- Center: {visual_data['region_analysis']['center']:.2%}
- Right: {visual_data['region_analysis']['right']:.2%}

What movement command should I use to get closer to trees?"""

    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            command = result.get("response", "").strip().lower()
            # Extract just the command letter
            if 'w' in command:
                return 'w'
            elif 'a' in command:
                return 'a'
            elif 's' in command:
                return 's'
            elif 'd' in command:
                return 'd'
            else:
                return 'stop'
        else:
            return 'stop'
            
    except Exception as e:
        print(f"❌ LLM failed: {e}")
        return 'stop'

def execute_movement(command, duration=1.0):
    """Execute movement command using pyautogui"""
    print(f"🎮 Executing: {command} for {duration}s")
    
    if command == 'stop':
        print("⏹️ Stopping")
        return
    
    try:
        # Focus window first (try iPhone Mirroring)
        print("🎯 Focusing Minecraft window...")
        pyautogui.click(800, 400)  # Click center of screen
        time.sleep(0.5)
        
        # Execute movement
        pyautogui.keyDown(command)
        time.sleep(duration)
        pyautogui.keyUp(command)
        print(f"✅ Moved {command} for {duration}s")
        
    except Exception as e:
        print(f"❌ Movement failed: {e}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Live Tree Navigation Test')
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Skip confirmation and start immediately (y/n)')
    args = parser.parse_args()
    
    print("🌳🎮 LIVE Tree Navigation Test")
    print("=" * 50)
    print("This will actually move your character!")
    
    # Safety confirmation
    if args.ready != 'y':
        print("❌ Use --ready y to start the test")
        print("Example: python test_live_tree_navigation.py --ready y")
        return
    
    print("\n🚀 Starting live navigation in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Run navigation loop
    for attempt in range(5):
        print(f"\n🔄 Navigation Step {attempt + 1}/5")
        
        # 1. Analyze current view
        visual_data = capture_and_analyze_for_trees()
        if not visual_data:
            print("❌ No visual data, skipping")
            continue
        
        # 2. Get movement command
        command = get_navigation_command(visual_data)
        print(f"📋 Command: {command}")
        
        # 3. Execute movement
        if command != 'stop':
            execute_movement(command, duration=1.5)
            
            # Wait a moment for movement to complete
            time.sleep(0.5)
        else:
            print("⏹️ No movement needed")
        
        # 4. Check if we should stop (close to trees)
        if visual_data['total_tree_coverage'] > 0.15:  # 15% tree coverage
            print("🎉 High tree coverage! Likely close to trees!")
            break
        
        # Brief pause between steps
        time.sleep(1)
    
    print("\n🏁 Live navigation test complete!")
    print("📁 Check 'live_tree_navigation.png' for final screenshot")

if __name__ == "__main__":
    main()