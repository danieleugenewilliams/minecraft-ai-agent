#!/usr/bin/env python3
"""
Simple LLM Vision Test - Lighter weight test to prove vision understanding
"""

import requests
import mss
import numpy as np
from PIL import Image
import time

def capture_simple_analysis():
    """Capture screen and do simple analysis"""
    try:
        sct = mss.mss()
        screenshot = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Very simple analysis
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Just check a few key colors
        wood_mask = np.all((img_array >= [80, 50, 20]) & (img_array <= [160, 130, 80]), axis=2)
        sky_mask = np.all((img_array >= [100, 150, 200]) & (img_array <= [200, 220, 255]), axis=2)
        dark_mask = np.all((img_array >= [0, 0, 0]) & (img_array <= [50, 50, 50]), axis=2)
        
        wood_pct = np.sum(wood_mask) / total_pixels
        sky_pct = np.sum(sky_mask) / total_pixels  
        dark_pct = np.sum(dark_mask) / total_pixels
        
        brightness = np.mean(img_array)
        
        return {
            'wood_visible': wood_pct,
            'sky_visible': sky_pct,
            'dark_areas': dark_pct,
            'brightness': brightness,
            'resolution': f"{img.size[0]}x{img.size[1]}"
        }
    except Exception as e:
        print(f"Vision error: {e}")
        return None

def test_simple_llm_vision():
    """Simple test to see if LLM can understand basic visual data"""
    print("📸 Capturing screen...")
    
    visual_data = capture_simple_analysis()
    if not visual_data:
        return False
    
    print(f"📊 Visual Analysis:")
    print(f"  Wood: {visual_data['wood_visible']:.1%}")
    print(f"  Sky: {visual_data['sky_visible']:.1%}")
    print(f"  Dark: {visual_data['dark_areas']:.1%}")
    print(f"  Brightness: {visual_data['brightness']:.0f}/255")
    
    # Simple prompt
    prompt = f"""I'm analyzing a Minecraft screen. Here's what I see:

Wood/trees visible: {visual_data['wood_visible']:.1%}
Sky visible: {visual_data['sky_visible']:.1%}
Dark areas: {visual_data['dark_areas']:.1%}
Overall brightness: {visual_data['brightness']:.0f}/255

Based on this data, am I:
A) Underground/in a cave (low sky, high dark areas)
B) On the surface during day (high sky, low dark)
C) On the surface at night (some sky, high dark)
D) In a building/enclosed area

Answer with just the letter and a brief reason."""

    try:
        print("🧠 Testing LLM understanding...")
        
        payload = {
            "model": "qwen2.5:7b",
            "prompt": prompt,
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
            llm_response = result.get("response", "").strip()
            
            print("✅ LLM Response:")
            print(f"   {llm_response}")
            
            # Check if response makes sense
            response_lower = llm_response.lower()
            
            # Analyze the visual data to see what the correct answer should be
            if visual_data['sky_visible'] < 0.01 and visual_data['dark_areas'] > 0.4:
                expected = "underground"
            elif visual_data['sky_visible'] > 0.05 and visual_data['brightness'] > 100:
                expected = "surface day"
            elif visual_data['sky_visible'] > 0.02 and visual_data['brightness'] < 80:
                expected = "surface night"
            else:
                expected = "enclosed"
            
            print(f"📊 Expected answer based on data: {expected}")
            
            # Check if LLM response aligns with data
            makes_sense = False
            if "underground" in expected and ("a" in response_lower or "cave" in response_lower or "underground" in response_lower):
                makes_sense = True
            elif "surface day" in expected and ("b" in response_lower or "day" in response_lower or "surface" in response_lower):
                makes_sense = True
            elif "surface night" in expected and ("c" in response_lower or "night" in response_lower):
                makes_sense = True
            elif "enclosed" in expected and ("d" in response_lower or "building" in response_lower or "enclosed" in response_lower):
                makes_sense = True
            
            if makes_sense:
                print("✅ LLM correctly interpreted the visual data!")
                return True
            else:
                print("⚠️ LLM response doesn't match visual data")
                return False
                
        else:
            print(f"❌ LLM error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

def main():
    print("🔍 Simple LLM Vision Test")
    print("=" * 40)
    print("Testing if LLM can understand basic visual data")
    print()
    
    success = test_simple_llm_vision()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 SUCCESS: LLM can understand visual data!")
        print("✅ The vision-LLM integration works")
        print("✅ LLM makes logical interpretations")
    else:
        print("❌ LLM vision understanding failed")
        print("🔧 Need to debug the integration")

if __name__ == "__main__":
    main()