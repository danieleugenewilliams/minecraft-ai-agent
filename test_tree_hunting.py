#!/usr/bin/env python3
"""
Tree Hunting Test
Agent actively searches for trees using movement + camera controls and gets close to them
"""

import requests
import mss
import numpy as np
from PIL import Image
import json
import time
import argparse
import pyautogui

def capture_and_analyze_for_trees():
    """Capture screen and perform detailed tree analysis"""
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Save with timestamp
        timestamp = int(time.time())
        filename = f"tree_hunt_{timestamp}.png"
        img.save(filename)
        
        # Enhanced tree detection
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # More precise tree color ranges (RGB)
        tree_colors = {
            'wood_logs': [(100, 60, 30), (180, 120, 80)],     # Brown wood logs
            'green_leaves': [(40, 100, 40), (140, 200, 140)], # Bright green leaves
            'dark_leaves': [(20, 60, 20), (100, 140, 100)],   # Darker leaves/shadows
            'tree_bark': [(80, 50, 25), (150, 100, 65)],      # Tree bark texture
        }
        
        tree_results = {}
        total_tree_coverage = 0
        
        for color_name, (lower, upper) in tree_colors.items():
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            coverage = np.sum(mask) / total_pixels
            tree_results[color_name] = coverage
            total_tree_coverage += coverage
        
        # Detailed region analysis for navigation
        height, width = img_array.shape[:2]
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3], 
            'right': img_array[:, 2*width//3:],
            'top': img_array[:height//3, :],
            'middle': img_array[height//3:2*height//3, :],
            'bottom': img_array[2*height//3:, :],
        }
        
        region_analysis = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            region_trees = 0
            
            for color_name, (lower, upper) in tree_colors.items():
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                region_trees += np.sum(mask) / region_pixels
            
            region_analysis[region_name] = region_trees
        
        # Find best direction for trees
        best_horizontal = max([('left', region_analysis['left']), 
                              ('center', region_analysis['center']), 
                              ('right', region_analysis['right'])], key=lambda x: x[1])
        
        best_vertical = max([('top', region_analysis['top']),
                            ('middle', region_analysis['middle']),
                            ('bottom', region_analysis['bottom'])], key=lambda x: x[1])
        
        return {
            'total_tree_coverage': total_tree_coverage,
            'tree_results': tree_results,
            'region_analysis': region_analysis,
            'best_horizontal': best_horizontal,
            'best_vertical': best_vertical,
            'filename': filename,
            'resolution': f"{width}x{height}"
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def get_llm_navigation_command(visual_data, step_num):
    """Ask LLM for smart navigation decision"""
    
    system_prompt = """You are a Minecraft navigation AI. Your goal is to find trees and get close to them.

Available commands:
MOVEMENT: w (forward), s (backward), a (left), d (right)
CAMERA: i (look up), k (look down), j (look left), l (look right)

Strategy:
1. If no trees visible (coverage < 2%), use camera to look around
2. If trees visible but low coverage (2-5%), move toward highest tree region
3. If good tree coverage (5%+), move forward to get closer

Respond with ONE command only."""

    regions = visual_data['region_analysis']
    coverage = visual_data['total_tree_coverage']
    best_h = visual_data['best_horizontal']
    best_v = visual_data['best_vertical']

    user_prompt = f"""Current situation:
- Total tree coverage: {coverage:.2%}
- Best horizontal region: {best_h[0]} ({best_h[1]:.2%})
- Best vertical region: {best_v[0]} ({best_v[1]:.2%})
- Step: {step_num}

Region breakdown:
- Left: {regions['left']:.1%}, Center: {regions['center']:.1%}, Right: {regions['right']:.1%}
- Top: {regions['top']:.1%}, Middle: {regions['middle']:.1%}, Bottom: {regions['bottom']:.1%}

What command should I execute to find and get closer to trees?"""

    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.2}
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "").strip().lower()
            
            # Extract command from response
            valid_commands = ['w', 's', 'a', 'd', 'i', 'k', 'j', 'l']
            for cmd in valid_commands:
                if cmd in llm_response:
                    return cmd
            
            # Fallback logic if LLM fails
            if coverage < 0.02:  # No trees - look around
                search_pattern = ['j', 'j', 'l', 'l', 'i', 'k']
                return search_pattern[step_num % len(search_pattern)]
            elif best_h[0] == 'left':
                return 'a'
            elif best_h[0] == 'right':
                return 'd'
            else:
                return 'w'
        else:
            return 'j'  # Default: look left
            
    except Exception as e:
        print(f"⚠️ LLM failed: {e}")
        return 'j'  # Default: look left

def execute_command(controller, command, duration=1.0):
    """Execute movement or camera command"""
    print(f"🎮 Executing: {command}")
    
    if controller is None:
        print(f"[SIMULATION] Would execute: {command}")
        return True
    
    try:
        # Focus Minecraft window
        if hasattr(controller, 'focus_minecraft_window'):
            controller.focus_minecraft_window()
        
        # Execute command
        if command in ['w', 'a', 's', 'd', 'i', 'k', 'j', 'l']:
            if hasattr(controller, 'key_tap'):
                controller.key_tap(command, duration=duration)
            else:
                controller.key_press(command)
                time.sleep(duration)
                controller.key_release(command)
        
        print(f"✅ Executed: {command}")
        return True
        
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Tree Hunting Agent')
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Start hunting immediately')
    parser.add_argument('--steps', type=int, default=15,
                       help='Number of hunting steps')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate without real input')
    args = parser.parse_args()
    
    print("🌳🏹 Tree Hunting Agent")
    print("=" * 50)
    print("Agent will search for trees and get close to them")
    print("Controls: w/a/s/d (move), i/k/j/l (look)")
    
    if args.ready != 'y':
        print("❌ Use --ready y to start hunting")
        print("Example: python test_tree_hunting.py --ready y --steps 15")
        return
    
    # Create input controller
    try:
        controller = create_input_controller(dry_run=args.dry_run)
        print(f"✅ Controller ready ({'DRY RUN' if args.dry_run else 'LIVE'})")
    except Exception as e:
        print(f"⚠️ Controller failed, using simulation: {e}")
        controller = None
    
    print(f"\n🚀 Starting {args.steps}-step tree hunt in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Hunting loop
    screenshots = []
    commands_executed = []
    max_tree_coverage = 0
    found_significant_trees = False
    
    for step in range(args.steps):
        print(f"\n🔄 Hunt Step {step + 1}/{args.steps}")
        
        # 1. Analyze environment
        visual_data = capture_and_analyze_for_trees()
        if not visual_data:
            print("❌ Skipping step")
            continue
        
        screenshots.append(visual_data['filename'])
        coverage = visual_data['total_tree_coverage']
        max_tree_coverage = max(max_tree_coverage, coverage)
        
        print(f"🌳 Tree coverage: {coverage:.2%}")
        print(f"📍 Best areas: {visual_data['best_horizontal'][0]} ({visual_data['best_horizontal'][1]:.1%}), "
              f"{visual_data['best_vertical'][0]} ({visual_data['best_vertical'][1]:.1%})")
        
        # 2. Check if we found significant trees
        if coverage > 0.08:  # 8% threshold for "found trees"
            print("🎉 SIGNIFICANT TREES FOUND!")
            found_significant_trees = True
            
            # If very close to trees, try to get even closer
            if visual_data['best_horizontal'][1] > 0.12:  # 12% in one region
                print("🎯 Getting closer to trees...")
                if visual_data['best_horizontal'][0] == 'left':
                    command = 'a'
                elif visual_data['best_horizontal'][0] == 'right':
                    command = 'd'
                else:
                    command = 'w'
            else:
                command = 'w'  # Move forward toward trees
        else:
            # 3. Get AI navigation command
            command = get_llm_navigation_command(visual_data, step)
        
        # 4. Execute command
        commands_executed.append(command)
        success = execute_command(controller, command, duration=1.2)
        
        if not success:
            print("⚠️ Command execution failed")
        
        # 5. Brief pause
        time.sleep(1.5)
        
        # 6. Stop if very close to trees
        if coverage > 0.15:  # 15% - very close
            print("🏆 VERY CLOSE TO TREES! Mission accomplished!")
            break
    
    # Final report
    print(f"\n🏁 Tree Hunt Complete!")
    print(f"Steps taken: {len(commands_executed)}")
    print(f"Commands: {' → '.join(commands_executed)}")
    print(f"Max tree coverage: {max_tree_coverage:.2%}")
    print(f"Screenshots: {len(screenshots)}")
    print(f"Significant trees found: {'✅ YES' if found_significant_trees else '❌ NO'}")
    
    if found_significant_trees:
        print("🎉 SUCCESS: Agent found and approached trees!")
    elif max_tree_coverage > 0.05:
        print("⚠️ Partial success: Agent detected trees but didn't get very close")
    else:
        print("❌ No significant trees found - try different starting position")
    
    print(f"📁 Final screenshots: {', '.join(screenshots[-3:])}")

if __name__ == "__main__":
    main()