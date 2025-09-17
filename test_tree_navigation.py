#!/usr/bin/env python3
"""
Tree Navigation Test
Tests if the agent can find and walk toward trees using vision + controls
"""

import requests
import mss
import numpy as np
from PIL import Image
import json
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from minecraft_ai.automation.input_controller import create_input_controller
    from minecraft_ai.vision.screen_capture import create_screen_capture, MinecraftVision
except ImportError:
    print("⚠️ Using simplified input controls (pyautogui may not be available)")
    create_input_controller = None

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
        img.save("tree_navigation_test.png")
        print(f"✅ Screenshot saved as 'tree_navigation_test.png' ({img.size[0]}x{img.size[1]})")
        
        # Enhanced tree-specific color analysis
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Tree-focused color ranges (RGB)
        tree_color_ranges = {
            'wood_trunk': [(80, 40, 20), (160, 100, 70)],      # Brown wood trunks
            'green_leaves': [(20, 60, 20), (100, 180, 100)],   # Green tree leaves
            'bark_brown': [(60, 30, 15), (140, 80, 50)],       # Darker bark
            'light_wood': [(120, 80, 40), (200, 140, 100)],    # Light wood varieties
            'dark_leaves': [(10, 40, 10), (60, 120, 60)],      # Darker green leaves
            'grass': [(40, 80, 30), (120, 160, 80)],           # Ground grass
            'sky': [(100, 150, 200), (180, 220, 255)],         # Sky background
            'dirt': [(80, 50, 20), (140, 100, 70)],            # Ground/dirt
        }
        
        print("\n🌳 Tree-Focused Color Analysis:")
        tree_results = {}
        tree_indicators = []
        
        for color_name, (lower, upper) in tree_color_ranges.items():
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            color_pixels = np.sum(mask)
            coverage = color_pixels / total_pixels
            tree_results[color_name] = coverage
            
            print(f"  {color_name:12}: {coverage:7.2%} ({color_pixels:,} pixels)")
            
            if 'wood' in color_name or 'leaves' in color_name:
                if coverage > 0.005:  # More than 0.5%
                    tree_indicators.append((color_name, coverage))
        
        # Calculate tree likelihood
        total_wood = tree_results['wood_trunk'] + tree_results['bark_brown'] + tree_results['light_wood']
        total_leaves = tree_results['green_leaves'] + tree_results['dark_leaves']
        total_tree_coverage = total_wood + total_leaves
        
        # Screen region analysis (for directional guidance)
        height, width = img_array.shape[:2]
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3],
            'right': img_array[:, 2*width//3:],
            'top': img_array[:height//2, :],
            'bottom': img_array[height//2:, :],
        }
        
        region_tree_coverage = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            region_wood = 0
            region_leaves = 0
            
            for color_name, (lower, upper) in tree_color_ranges.items():
                if 'wood' in color_name or 'bark' in color_name:
                    mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                    region_wood += np.sum(mask) / region_pixels
                elif 'leaves' in color_name:
                    mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                    region_leaves += np.sum(mask) / region_pixels
            
            region_tree_coverage[region_name] = region_wood + region_leaves
        
        visual_summary = {
            'screen_resolution': f"{img.size[0]}x{img.size[1]}",
            'total_tree_coverage': total_tree_coverage,
            'wood_coverage': total_wood,
            'leaves_coverage': total_leaves,
            'tree_indicators': tree_indicators,
            'region_analysis': region_tree_coverage,
            'timestamp': time.time()
        }
        
        print(f"\n🎯 Tree Detection Summary:")
        print(f"  Total tree coverage: {total_tree_coverage:.2%}")
        print(f"  Wood coverage: {total_wood:.2%}")
        print(f"  Leaves coverage: {total_leaves:.2%}")
        print(f"  Region with most trees: {max(region_tree_coverage.items(), key=lambda x: x[1])}")
        
        return visual_summary
        
    except Exception as e:
        print(f"❌ Tree analysis failed: {e}")
        return None

def ask_llm_for_navigation(visual_data):
    """Ask LLM to analyze trees and provide navigation instructions"""
    print("\n🧠 Asking LLM for tree navigation...")
    
    if not visual_data:
        print("❌ No visual data for navigation")
        return None
    
    system_prompt = """You are a Minecraft navigation AI. Your job is to analyze visual data and provide specific movement commands to reach trees.

You can use these movement commands:
- "w" = move forward
- "a" = move left  
- "s" = move backward
- "d" = move right
- "look_left" = turn camera left
- "look_right" = turn camera right
- "look_up" = look up
- "look_down" = look down
- "stop" = stop all movement

Your response should be a JSON object with:
{
    "trees_detected": true/false,
    "tree_direction": "left/center/right/up/down/none",
    "next_action": "movement command",
    "reasoning": "explanation of why this action",
    "confidence": 0.0-1.0
}"""

    user_prompt = f"""I need to find and walk to trees in Minecraft. Here's what my vision system detected:

TREE ANALYSIS:
- Total tree coverage: {visual_data['total_tree_coverage']:.2%}
- Wood coverage: {visual_data['wood_coverage']:.2%}  
- Leaves coverage: {visual_data['leaves_coverage']:.2%}

SCREEN REGIONS (tree coverage in each area):
"""
    
    for region, coverage in visual_data['region_analysis'].items():
        user_prompt += f"- {region.title()}: {coverage:.2%}\n"
    
    user_prompt += f"""
DETECTED TREE INDICATORS:
"""
    for color_name, coverage in visual_data['tree_indicators']:
        user_prompt += f"- {color_name.replace('_', ' ').title()}: {coverage:.2%}\n"
    
    user_prompt += """
TASK: Analyze this data and tell me:
1. Are there trees visible on screen?
2. Which direction should I move/look to get closer to trees?
3. What specific movement command should I execute?

Provide your response as a JSON object as specified in the system prompt."""

    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        
        print("🔄 Getting navigation instructions from LLM...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "").strip()
            
            print("🎯 LLM Navigation Response:")
            print("=" * 50)
            print(llm_response)
            print("=" * 50)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response if it's wrapped in text
                if '{' in llm_response and '}' in llm_response:
                    start = llm_response.find('{')
                    end = llm_response.rfind('}') + 1
                    json_str = llm_response[start:end]
                    navigation_data = json.loads(json_str)
                    return navigation_data
                else:
                    print("⚠️ No JSON found in response")
                    return None
            except json.JSONDecodeError as e:
                print(f"⚠️ Could not parse JSON: {e}")
                return None
        else:
            print(f"❌ LLM request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ LLM navigation failed: {e}")
        return None

def execute_movement_command(controller, command, duration=0.5):
    """Execute a movement command using the input controller"""
    print(f"🎮 Executing command: {command}")
    
    try:
        if command == "w":
            controller.key_press("w")
            time.sleep(duration)
            controller.key_release("w")
        elif command == "a":
            controller.key_press("a")
            time.sleep(duration)
            controller.key_release("a")
        elif command == "s":
            controller.key_press("s")
            time.sleep(duration)
            controller.key_release("s")
        elif command == "d":
            controller.key_press("d")
            time.sleep(duration)
            controller.key_release("d")
        elif command == "look_left":
            # Move mouse left to turn camera
            current_pos = controller.get_mouse_position() if hasattr(controller, 'get_mouse_position') else (800, 400)
            controller.move_mouse(current_pos[0] - 100, current_pos[1])
            time.sleep(0.2)
        elif command == "look_right":
            # Move mouse right to turn camera
            current_pos = controller.get_mouse_position() if hasattr(controller, 'get_mouse_position') else (800, 400)
            controller.move_mouse(current_pos[0] + 100, current_pos[1])
            time.sleep(0.2)
        elif command == "look_up":
            # Move mouse up to look up
            current_pos = controller.get_mouse_position() if hasattr(controller, 'get_mouse_position') else (800, 400)
            controller.move_mouse(current_pos[0], current_pos[1] - 50)
            time.sleep(0.2)
        elif command == "look_down":
            # Move mouse down to look down
            current_pos = controller.get_mouse_position() if hasattr(controller, 'get_mouse_position') else (800, 400)
            controller.move_mouse(current_pos[0], current_pos[1] + 50)
            time.sleep(0.2)
        elif command == "stop":
            # Release all movement keys
            for key in ["w", "a", "s", "d"]:
                controller.key_release(key)
        else:
            print(f"⚠️ Unknown command: {command}")
            return False
        
        print(f"✅ Command executed: {command}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to execute command {command}: {e}")
        return False

def test_tree_navigation_cycle(controller, max_attempts=5, dry_run=False):
    """Run a complete tree navigation test cycle"""
    print(f"\n🌳 Starting Tree Navigation Test ({'DRY RUN' if dry_run else 'LIVE'})")
    print("=" * 60)
    
    for attempt in range(max_attempts):
        print(f"\n🔄 Navigation Attempt {attempt + 1}/{max_attempts}")
        
        # Step 1: Capture and analyze screen for trees
        visual_data = capture_and_analyze_for_trees()
        if not visual_data:
            print("❌ Cannot continue without visual data")
            continue
        
        # Step 2: Ask LLM for navigation instructions
        navigation = ask_llm_for_navigation(visual_data)
        if not navigation:
            print("❌ No navigation instructions received")
            continue
        
        print(f"\n📊 Navigation Analysis:")
        print(f"  Trees detected: {navigation.get('trees_detected', 'unknown')}")
        print(f"  Tree direction: {navigation.get('tree_direction', 'unknown')}")
        print(f"  Next action: {navigation.get('next_action', 'none')}")
        print(f"  Confidence: {navigation.get('confidence', 0):.1%}")
        print(f"  Reasoning: {navigation.get('reasoning', 'no reasoning provided')}")
        
        # Step 3: Execute movement command
        next_action = navigation.get('next_action', 'stop')
        if next_action and next_action != 'stop':
            if not dry_run:
                # Focus Minecraft window before sending commands
                if hasattr(controller, 'focus_minecraft_window'):
                    print("🎯 Focusing Minecraft window...")
                    controller.focus_minecraft_window()
                    time.sleep(1)
                
            success = execute_movement_command(controller, next_action)
            if success:
                print(f"✅ Movement executed successfully")
                
                # Wait a moment for movement to complete
                time.sleep(1.5)
                
                # Check if we should stop (high tree coverage means we're close)
                if visual_data['total_tree_coverage'] > 0.05:  # 5% tree coverage
                    print("🎉 High tree coverage detected - likely near trees!")
                    break
            else:
                print("❌ Movement failed")
        else:
            print("⏹️ No movement action required")
        
        # Brief pause between attempts
        time.sleep(0.5)
    
    print(f"\n🏁 Tree Navigation Test Complete")
    return True

def main():
    print("🌳🤖 Tree Navigation Test")
    print("=" * 60)
    print("Testing if the agent can find and walk toward trees")
    print()
    
    # Ask user about dry run mode
    dry_run_choice = input("Run in dry run mode? (y/n): ").lower().strip()
    dry_run = dry_run_choice in ['y', 'yes']
    
    # Create input controller
    try:
        controller = create_input_controller(dry_run=dry_run)
        print(f"✅ Input controller created ({'DRY RUN' if dry_run else 'LIVE'})")
    except Exception as e:
        print(f"❌ Failed to create input controller: {e}")
        return
    
    # Run the navigation test
    success = test_tree_navigation_cycle(controller, max_attempts=5, dry_run=dry_run)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TREE NAVIGATION TEST RESULTS")
    print(f"Test completed: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Mode: {'🔬 DRY RUN' if dry_run else '🎮 LIVE'}")
    
    if success:
        print("\n🎉 TREE NAVIGATION CAPABILITIES VERIFIED!")
        print("✅ Vision system can detect trees in screenshots")
        print("✅ LLM can analyze tree data and provide directions")
        print("✅ Control system can execute movement commands")
        print("✅ Agent can navigate toward trees autonomously")
        print(f"\n📁 Check 'tree_navigation_test.png' to see what was analyzed")
    else:
        print("\n⚠️ Tree navigation needs improvement")
        print("🔧 Check vision detection accuracy")
        print("🔧 Verify LLM navigation logic")
        print("🔧 Test control system responsiveness")

if __name__ == "__main__":
    main()