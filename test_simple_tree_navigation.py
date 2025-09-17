#!/usr/bin/env python3
"""
Simple Tree Navigation Test
Tests if LLM can detect trees and provide navigation directions
"""

import requests
import mss
import numpy as np
from PIL import Image
import json
import time

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
        if region_tree_coverage:
            best_region = max(region_tree_coverage.items(), key=lambda x: x[1])
            print(f"  Region with most trees: {best_region[0]} ({best_region[1]:.2%})")
        
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
- "stop" = stop all movement

Your response should be a JSON object with:
{
    "trees_detected": true/false,
    "tree_direction": "left/center/right/none",
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
                # Create fallback response based on text analysis
                fallback = {
                    "trees_detected": "tree" in llm_response.lower() or "wood" in llm_response.lower(),
                    "tree_direction": "center",
                    "next_action": "w" if "forward" in llm_response.lower() else "stop",
                    "reasoning": "Fallback analysis of text response",
                    "confidence": 0.5
                }
                return fallback
        else:
            print(f"❌ LLM request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ LLM navigation failed: {e}")
        return None

def main():
    print("🌳🤖 Simple Tree Navigation Test")
    print("=" * 60)
    print("Testing if the LLM can detect trees and provide navigation directions")
    print()
    
    # Step 1: Capture and analyze screen for trees
    print("Step 1: Analyzing screen for trees...")
    visual_data = capture_and_analyze_for_trees()
    if not visual_data:
        print("❌ Cannot continue without visual data")
        return
    
    # Step 2: Ask LLM for navigation instructions
    print("\nStep 2: Getting navigation instructions...")
    navigation = ask_llm_for_navigation(visual_data)
    if not navigation:
        print("❌ No navigation instructions received")
        return
    
    # Step 3: Display results
    print(f"\n📊 Navigation Analysis Results:")
    print(f"  Trees detected: {navigation.get('trees_detected', 'unknown')}")
    print(f"  Tree direction: {navigation.get('tree_direction', 'unknown')}")
    print(f"  Recommended action: {navigation.get('next_action', 'none')}")
    print(f"  Confidence: {navigation.get('confidence', 0):.1%}")
    print(f"  Reasoning: {navigation.get('reasoning', 'no reasoning provided')}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TREE NAVIGATION TEST RESULTS")
    
    trees_found = visual_data['total_tree_coverage'] > 0.01  # More than 1%
    llm_detected_trees = navigation.get('trees_detected', False)
    has_action = navigation.get('next_action', 'stop') != 'stop'
    
    print(f"Tree Coverage Detected: {'✅' if trees_found else '❌'} ({visual_data['total_tree_coverage']:.2%})")
    print(f"LLM Detected Trees: {'✅' if llm_detected_trees else '❌'}")
    print(f"Navigation Action Provided: {'✅' if has_action else '❌'}")
    
    if trees_found and llm_detected_trees and has_action:
        print("\n🎉 TREE NAVIGATION TEST PASSED!")
        print("✅ Vision system detects trees")
        print("✅ LLM correctly identifies trees")
        print("✅ LLM provides navigation instructions")
        print("✅ Ready for control integration!")
    else:
        print("\n⚠️ Tree navigation needs improvement")
        if not trees_found:
            print("🔧 No significant trees visible in current view")
        if not llm_detected_trees:
            print("🔧 LLM failed to detect trees in analysis")
        if not has_action:
            print("🔧 LLM provided no actionable navigation command")
    
    print(f"\n📁 Screenshot saved as 'tree_navigation_test.png'")

if __name__ == "__main__":
    main()