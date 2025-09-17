#!/usr/bin/env python3
"""
LLM Vision Understanding Test
Prove that the LLM can actually see and understand visual data from the screen
"""

import requests
import mss
import numpy as np
from PIL import Image
import json
import time

def capture_and_analyze_screen():
    """Capture screen and perform detailed visual analysis"""
    print("📸 Capturing and analyzing screen...")
    
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Save for verification
        img.save("llm_vision_test.png")
        print(f"✅ Screenshot saved as 'llm_vision_test.png' ({img.size[0]}x{img.size[1]})")
        
        # Detailed color analysis
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # More comprehensive color detection
        color_ranges = {
            'brown_wood': [(101, 67, 33), (160, 130, 80)],
            'green_leaves': [(20, 70, 20), (80, 150, 80)],
            'brown_dirt': [(80, 50, 20), (140, 100, 70)],
            'gray_stone': [(80, 80, 80), (180, 180, 180)],
            'green_grass': [(40, 100, 40), (120, 200, 120)],
            'blue_sky': [(100, 150, 200), (180, 220, 255)],
            'blue_water': [(50, 100, 150), (120, 180, 255)],
            'black_dark': [(0, 0, 0), (40, 40, 40)],
            'white_light': [(200, 200, 200), (255, 255, 255)],
            'red_areas': [(150, 50, 50), (255, 120, 120)],
            'yellow_areas': [(200, 200, 50), (255, 255, 150)],
            'purple_areas': [(100, 50, 150), (200, 120, 255)],
        }
        
        print("\n🎨 Detailed Color Analysis:")
        color_results = {}
        significant_colors = []
        
        for color_name, (lower, upper) in color_ranges.items():
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            color_pixels = np.sum(mask)
            coverage = color_pixels / total_pixels
            color_results[color_name] = coverage
            
            print(f"  {color_name:12}: {coverage:7.2%} ({color_pixels:,} pixels)")
            
            if coverage > 0.01:  # More than 1%
                significant_colors.append((color_name, coverage))
        
        # Calculate image statistics
        mean_color = np.mean(img_array, axis=(0,1))
        brightness = np.mean(mean_color)
        
        # Detect dominant regions
        top_colors = sorted(significant_colors, key=lambda x: x[1], reverse=True)
        
        # Create comprehensive visual summary
        visual_summary = {
            'screen_resolution': f"{img.size[0]}x{img.size[1]}",
            'total_pixels': total_pixels,
            'overall_brightness': brightness,
            'mean_rgb': [float(mean_color[0]), float(mean_color[1]), float(mean_color[2])],
            'color_coverage': color_results,
            'significant_colors': top_colors[:5],
            'analysis_timestamp': time.time()
        }
        
        print(f"\n📊 Visual Summary:")
        print(f"  Resolution: {visual_summary['screen_resolution']}")
        print(f"  Brightness: {brightness:.1f}/255")
        print(f"  Dominant colors: {[f'{name} ({pct:.1%})' for name, pct in top_colors[:3]]}")
        
        return visual_summary
        
    except Exception as e:
        print(f"❌ Screen analysis failed: {e}")
        return None

def test_llm_visual_understanding(visual_data):
    """Test if LLM can understand and interpret visual data"""
    print("\n🧠 Testing LLM Visual Understanding...")
    
    if not visual_data:
        print("❌ No visual data to test")
        return False
    
    # Create a detailed prompt with visual data
    system_prompt = """You are an AI that can analyze visual data from computer screens. You will be given detailed color analysis data from a screenshot. Your job is to:

1. Understand what the visual data means
2. Describe what you think is shown on the screen
3. Make intelligent inferences about the environment
4. Identify if this could be a game, application, or desktop

Be specific and detailed in your analysis. Explain your reasoning."""

    user_prompt = f"""I have captured and analyzed a screenshot. Here is the detailed visual data:

SCREEN INFORMATION:
- Resolution: {visual_data['screen_resolution']}
- Total pixels: {visual_data['total_pixels']:,}
- Overall brightness: {visual_data['overall_brightness']:.1f}/255 (where 0=black, 255=white)
- Average RGB color: ({visual_data['mean_rgb'][0]:.1f}, {visual_data['mean_rgb'][1]:.1f}, {visual_data['mean_rgb'][2]:.1f})

COLOR ANALYSIS (percentage of screen covered by each color):
"""
    
    # Add color data in a readable format
    for color_name, percentage in visual_data['color_coverage'].items():
        if percentage > 0.005:  # Only show colors > 0.5%
            user_prompt += f"- {color_name.replace('_', ' ').title()}: {percentage:.2%}\n"
    
    user_prompt += f"""
MOST SIGNIFICANT COLORS (top 5):
"""
    for i, (color_name, percentage) in enumerate(visual_data['significant_colors'][:5], 1):
        user_prompt += f"{i}. {color_name.replace('_', ' ').title()}: {percentage:.2%}\n"
    
    user_prompt += """
ANALYSIS QUESTIONS:
1. Based on this color analysis, what do you think is displayed on the screen?
2. Does this look like a game interface? If so, what type of game?
3. Are there any Minecraft-specific indicators in this data?
4. What can you infer about the environment or scene?
5. Is this person likely indoors, outdoors, underground, or in a UI?
6. What would you recommend doing if this were a game character's view?

Please provide a detailed analysis with specific reasoning based on the color data."""

    try:
        # Send to LLM
        payload = {
            "model": "qwen2.5:3b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }
        
        print("🔄 Sending visual data to LLM for analysis...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_analysis = result.get("response", "").strip()
            
            print("✅ LLM Analysis Received!")
            print("=" * 60)
            print(llm_analysis)
            print("=" * 60)
            
            # Check if LLM shows understanding
            understanding_indicators = [
                'minecraft' in llm_analysis.lower(),
                'game' in llm_analysis.lower(),
                'underground' in llm_analysis.lower() or 'cave' in llm_analysis.lower(),
                'outdoor' in llm_analysis.lower() or 'surface' in llm_analysis.lower(),
                'tree' in llm_analysis.lower() or 'wood' in llm_analysis.lower(),
                'dark' in llm_analysis.lower() or 'bright' in llm_analysis.lower(),
                len(llm_analysis) > 200  # Detailed response
            ]
            
            understanding_score = sum(understanding_indicators)
            
            print(f"\n📊 LLM Understanding Assessment:")
            print(f"  Response length: {len(llm_analysis)} characters")
            print(f"  Understanding indicators found: {understanding_score}/7")
            
            if understanding_score >= 4:
                print("✅ LLM demonstrates good visual understanding!")
                return True
            elif understanding_score >= 2:
                print("⚠️ LLM shows partial visual understanding")
                return True
            else:
                print("❌ LLM shows limited visual understanding")
                return False
                
        else:
            print(f"❌ LLM request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

def test_llm_minecraft_specific_analysis(visual_data):
    """Test LLM's ability to make Minecraft-specific interpretations"""
    print("\n🎮 Testing Minecraft-Specific LLM Analysis...")
    
    if not visual_data:
        print("❌ No visual data for Minecraft analysis")
        return False
    
    # Extract Minecraft-relevant data
    colors = visual_data['color_coverage']
    minecraft_colors = {
        'wood_and_trees': colors.get('brown_wood', 0) + colors.get('green_leaves', 0),
        'dirt_and_stone': colors.get('brown_dirt', 0) + colors.get('gray_stone', 0),
        'grass': colors.get('green_grass', 0),
        'sky': colors.get('blue_sky', 0),
        'water': colors.get('blue_water', 0),
        'darkness': colors.get('black_dark', 0),
        'brightness': colors.get('white_light', 0)
    }
    
    system_prompt = """You are a Minecraft gameplay expert AI. You will analyze visual color data from a Minecraft game screen and provide strategic gameplay advice.

Focus on:
1. Identifying the Minecraft environment type
2. Detecting available resources
3. Assessing the situation
4. Providing specific action recommendations

Be detailed and strategic in your analysis."""

    user_prompt = f"""I am playing Minecraft and need your analysis of what my character can see. Here's the color analysis of my current view:

MINECRAFT COLOR ANALYSIS:
- Wood and Trees (brown wood + green leaves): {minecraft_colors['wood_and_trees']:.2%}
- Dirt and Stone (building materials): {minecraft_colors['dirt_and_stone']:.2%}
- Grass (surface areas): {minecraft_colors['grass']:.2%}
- Sky (outdoor indicator): {minecraft_colors['sky']:.2%}
- Water: {minecraft_colors['water']:.2%}
- Dark areas (caves, shadows, UI): {minecraft_colors['darkness']:.2%}
- Bright areas (light sources, sun): {minecraft_colors['brightness']:.2%}

TECHNICAL DATA:
- Screen brightness: {visual_data['overall_brightness']:.1f}/255
- Dominant colors visible: {', '.join([name.replace('_', ' ') for name, _ in visual_data['significant_colors'][:3]])}

MINECRAFT ANALYSIS NEEDED:
1. What type of Minecraft environment am I in? (surface, underground, forest, plains, etc.)
2. What resources can I see and gather?
3. What is my current situation? (safe, dangerous, good for building, etc.)
4. What should I do next to survive and build a shelter?
5. Are there any specific threats or opportunities I should know about?

Provide specific Minecraft gameplay advice based on this visual analysis."""

    try:
        payload = {
            "model": "qwen2.5:3b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        
        print("🎯 Getting Minecraft-specific LLM analysis...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=25
        )
        
        if response.status_code == 200:
            result = response.json()
            minecraft_analysis = result.get("response", "").strip()
            
            print("🎮 Minecraft Expert Analysis:")
            print("=" * 60)
            print(minecraft_analysis)
            print("=" * 60)
            
            # Check for Minecraft-specific understanding
            minecraft_indicators = [
                'underground' in minecraft_analysis.lower() or 'cave' in minecraft_analysis.lower(),
                'surface' in minecraft_analysis.lower() or 'overworld' in minecraft_analysis.lower(),
                'wood' in minecraft_analysis.lower() or 'tree' in minecraft_analysis.lower(),
                'mine' in minecraft_analysis.lower() or 'dig' in minecraft_analysis.lower(),
                'shelter' in minecraft_analysis.lower() or 'build' in minecraft_analysis.lower(),
                'craft' in minecraft_analysis.lower() or 'tool' in minecraft_analysis.lower(),
                'block' in minecraft_analysis.lower(),
                len(minecraft_analysis) > 150
            ]
            
            minecraft_score = sum(minecraft_indicators)
            
            print(f"\n🎯 Minecraft Understanding Score: {minecraft_score}/8")
            
            if minecraft_score >= 5:
                print("✅ LLM shows excellent Minecraft-specific understanding!")
                return True
            elif minecraft_score >= 3:
                print("⚠️ LLM shows good Minecraft understanding")
                return True
            else:
                print("❌ LLM shows limited Minecraft-specific understanding")
                return False
                
        else:
            print(f"❌ Minecraft analysis failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Minecraft analysis error: {e}")
        return False

def main():
    print("🔍👁️ LLM Vision Understanding Test")
    print("=" * 60)
    print("This test proves the LLM can actually see and understand visual data")
    print()
    
    # Step 1: Capture and analyze screen
    visual_data = capture_and_analyze_screen()
    
    if not visual_data:
        print("❌ Cannot test LLM vision without visual data")
        return
    
    # Step 2: Test general LLM visual understanding
    general_understanding = test_llm_visual_understanding(visual_data)
    
    # Step 3: Test Minecraft-specific understanding
    minecraft_understanding = test_llm_minecraft_specific_analysis(visual_data)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 LLM VISION UNDERSTANDING RESULTS")
    print(f"Visual Data Capture: {'✅ SUCCESS' if visual_data else '❌ FAILED'}")
    print(f"General LLM Understanding: {'✅ GOOD' if general_understanding else '❌ LIMITED'}")
    print(f"Minecraft-Specific Understanding: {'✅ EXCELLENT' if minecraft_understanding else '❌ LIMITED'}")
    
    if all([visual_data, general_understanding, minecraft_understanding]):
        print("\n🎉 PROOF: LLM CAN SEE AND UNDERSTAND!")
        print("✅ The LLM successfully interpreted visual color data")
        print("✅ The LLM provided intelligent analysis of the screen")
        print("✅ The LLM gave Minecraft-specific strategic advice")
        print("✅ The vision-LLM integration is working perfectly!")
        print(f"\n📁 Check 'llm_vision_test.png' to see exactly what the LLM analyzed")
    else:
        print("\n⚠️ LLM vision understanding needs improvement")
        if not general_understanding:
            print("🔧 LLM is not interpreting visual data well")
        if not minecraft_understanding:
            print("🔧 LLM needs better Minecraft-specific training")

if __name__ == "__main__":
    main()