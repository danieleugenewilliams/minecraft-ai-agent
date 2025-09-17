#!/usr/bin/env python3
"""
Real Tree Search Test
Forces the agent to actively search for trees and navigate toward them
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
    print("📸 Capturing screen...")
    
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Save for verification
        timestamp = int(time.time())
        filename = f"tree_search_{timestamp}.png"
        img.save(filename)
        print(f"✅ Screenshot: {filename}")
        
        # Tree-focused color analysis
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # More strict tree detection
        tree_color_ranges = {
            'wood_trunk': [(80, 40, 20), (160, 100, 70)],
            'green_leaves': [(30, 80, 30), (120, 200, 120)],  # More specific green
            'dark_leaves': [(20, 60, 20), (80, 140, 80)],
        }
        
        tree_results = {}
        for color_name, (lower, upper) in tree_color_ranges.items():
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            coverage = np.sum(mask) / total_pixels
            tree_results[color_name] = coverage
        
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
        
        print(f"🌳 Tree coverage: {total_tree_coverage:.2%}")
        print(f"   L:{region_tree_coverage['left']:.1%} C:{region_tree_coverage['center']:.1%} R:{region_tree_coverage['right']:.1%}")
        
        return {
            'total_tree_coverage': total_tree_coverage,
            'region_analysis': region_tree_coverage,
            'tree_results': tree_results,
            'filename': filename
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def get_search_command(visual_data, step_num):
    """Get search command - prioritize exploration if no trees found"""
    trees_found = visual_data['total_tree_coverage'] > 0.03  # 3% threshold
    
    if not trees_found:
        # No trees found - search pattern
        search_commands = ['look_right', 'look_right', 'w', 'look_left', 'look_left', 'w']
        command = search_commands[step_num % len(search_commands)]
        print(f"🔍 No trees found - searching: {command}")
        return command
    else:
        # Trees found - navigate toward them
        regions = visual_data['region_analysis']
        if regions['left'] > regions['center'] and regions['left'] > regions['right']:
            return 'a'  # Move left
        elif regions['right'] > regions['center'] and regions['right'] > regions['left']:
            return 'd'  # Move right
        else:
            return 'w'  # Move forward

def execute_movement(command, duration=1.0):
    """Execute movement command"""
    print(f"🎮 Executing: {command}")
    
    try:
        # Focus window
        pyautogui.click(800, 400)
        time.sleep(0.2)
        
        if command in ['w', 'a', 's', 'd']:
            # Movement keys
            pyautogui.keyDown(command)
            time.sleep(duration)
            pyautogui.keyUp(command)
        elif command == 'look_right':
            # Turn camera right
            pyautogui.moveRel(200, 0, duration=0.3)
        elif command == 'look_left':
            # Turn camera left
            pyautogui.moveRel(-200, 0, duration=0.3)
        elif command == 'look_up':
            # Look up
            pyautogui.moveRel(0, -100, duration=0.3)
        elif command == 'look_down':
            # Look down
            pyautogui.moveRel(0, 100, duration=0.3)
        
        print(f"✅ Executed: {command}")
        return True
        
    except Exception as e:
        print(f"❌ Movement failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Real Tree Search Test')
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Start immediately (y/n)')
    parser.add_argument('--steps', type=int, default=10,
                       help='Number of search steps')
    args = parser.parse_args()
    
    print("🔍🌳 REAL Tree Search Test")
    print("=" * 50)
    print("Agent will actively search for trees and navigate to them")
    
    if args.ready != 'y':
        print("❌ Use --ready y to start")
        print("Example: python test_real_tree_search.py --ready y --steps 10")
        return
    
    print(f"\n🚀 Starting {args.steps}-step tree search in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    trees_found = False
    screenshots = []
    
    # Main search loop
    for step in range(args.steps):
        print(f"\n🔄 Search Step {step + 1}/{args.steps}")
        
        # 1. Analyze current view
        visual_data = capture_and_analyze_for_trees()
        if not visual_data:
            print("❌ Skipping step")
            continue
        
        screenshots.append(visual_data['filename'])
        
        # 2. Check if we found significant trees
        if visual_data['total_tree_coverage'] > 0.05:  # 5% threshold
            print("🎉 TREES FOUND! High tree coverage detected!")
            trees_found = True
            
            # Try to get closer
            regions = visual_data['region_analysis']
            if max(regions.values()) > 0.08:  # 8% in one region
                best_region = max(regions.items(), key=lambda x: x[1])
                print(f"🎯 Moving toward trees in {best_region[0]} region")
                
                if best_region[0] == 'left':
                    execute_movement('a', 2.0)
                elif best_region[0] == 'right':
                    execute_movement('d', 2.0)
                else:
                    execute_movement('w', 2.0)
            break
        
        # 3. Get search command
        command = get_search_command(visual_data, step)
        
        # 4. Execute movement
        execute_movement(command, 1.5)
        
        # 5. Wait between actions
        time.sleep(1)
    
    # Final analysis
    print(f"\n🏁 Tree Search Complete!")
    print(f"Trees found: {'✅ YES' if trees_found else '❌ NO'}")
    print(f"Screenshots taken: {len(screenshots)}")
    print(f"Search steps executed: {len(screenshots)}")
    
    if trees_found:
        print("🎉 SUCCESS: Agent searched and found trees!")
    else:
        print("⚠️ Agent searched but didn't find significant trees")
        print("Try positioning in an area with more visible trees")
    
    print(f"📁 Screenshots: {', '.join(screenshots[-3:])}")  # Show last 3

if __name__ == "__main__":
    main()