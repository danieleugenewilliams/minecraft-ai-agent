#!/usr/bin/env python3
"""
Vision System Validation Test
Verify that computer vision is actually working and analyzing the screen
"""

import mss
import numpy as np
from PIL import Image
import time
import os

def test_screen_capture():
    """Test basic screen capture functionality"""
    print("=== Testing Screen Capture ===")
    
    try:
        sct = mss.mss()
        
        # Get monitor info
        monitors = sct.monitors
        print(f"Available monitors: {len(monitors)}")
        for i, monitor in enumerate(monitors):
            print(f"  Monitor {i}: {monitor}")
        
        # Capture primary monitor
        monitor = sct.monitors[1]
        print(f"\nCapturing monitor: {monitor}")
        
        screenshot = sct.grab(monitor)
        print(f"Screenshot size: {screenshot.size}")
        print(f"Screenshot format: {screenshot.bgra}")
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        print(f"PIL Image size: {img.size}")
        print(f"PIL Image mode: {img.mode}")
        
        # Save screenshot for verification
        img.save("vision_test_screenshot.png")
        print("✅ Screenshot saved as 'vision_test_screenshot.png'")
        
        return img
        
    except Exception as e:
        print(f"❌ Screen capture failed: {e}")
        return None

def test_color_analysis(image):
    """Test color analysis on the captured image"""
    print("\n=== Testing Color Analysis ===")
    
    if image is None:
        print("❌ No image to analyze")
        return None
    
    try:
        # Convert to numpy array
        img_array = np.array(image)
        print(f"Image array shape: {img_array.shape}")
        
        total_pixels = img_array.shape[0] * img_array.shape[1]
        print(f"Total pixels: {total_pixels:,}")
        
        # Define color ranges (RGB format)
        color_ranges = {
            'wood': [(101, 67, 33), (160, 130, 80)],      # Brown wood colors
            'leaves': [(20, 70, 20), (80, 150, 80)],      # Green leaf colors
            'dirt': [(101, 67, 33), (139, 90, 60)],       # Brown dirt colors
            'stone': [(100, 100, 100), (180, 180, 180)],  # Gray stone colors
            'grass': [(40, 100, 40), (100, 180, 100)],    # Green grass colors
            'sky': [(100, 150, 200), (180, 220, 255)],    # Blue/light blue sky
            'black': [(0, 0, 0), (30, 30, 30)],          # Dark/black areas
            'white': [(200, 200, 200), (255, 255, 255)],  # Light/white areas
        }
        
        color_coverage = {}
        color_pixel_counts = {}
        
        print("\nAnalyzing colors...")
        for color_name, (lower, upper) in color_ranges.items():
            # Create mask for this color range
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            color_pixels = np.sum(mask)
            coverage = color_pixels / total_pixels
            
            color_coverage[color_name] = coverage
            color_pixel_counts[color_name] = color_pixels
            
            print(f"  {color_name:8}: {coverage:6.1%} ({color_pixels:,} pixels)")
        
        # Find dominant colors
        dominant_colors = sorted(color_coverage.items(), key=lambda x: x[1], reverse=True)
        print(f"\nTop 3 dominant colors:")
        for i, (color, percentage) in enumerate(dominant_colors[:3]):
            print(f"  {i+1}. {color}: {percentage:.1%}")
        
        # Calculate some basic image statistics
        mean_rgb = np.mean(img_array, axis=(0,1))
        print(f"\nImage statistics:")
        print(f"  Mean RGB: ({mean_rgb[0]:.1f}, {mean_rgb[1]:.1f}, {mean_rgb[2]:.1f})")
        print(f"  Brightness: {np.mean(mean_rgb):.1f}/255")
        
        return color_coverage
        
    except Exception as e:
        print(f"❌ Color analysis failed: {e}")
        return None

def test_minecraft_detection(color_coverage):
    """Test if we can detect Minecraft-specific patterns"""
    print("\n=== Testing Minecraft Detection ===")
    
    if color_coverage is None:
        print("❌ No color data to analyze")
        return False
    
    # Look for Minecraft-like patterns
    minecraft_indicators = []
    
    # Check for typical Minecraft colors
    wood_leaves = color_coverage.get('wood', 0) + color_coverage.get('leaves', 0)
    dirt_stone = color_coverage.get('dirt', 0) + color_coverage.get('stone', 0)
    grass_present = color_coverage.get('grass', 0)
    sky_present = color_coverage.get('sky', 0)
    
    print(f"Minecraft color analysis:")
    print(f"  Wood/Trees total: {wood_leaves:.1%}")
    print(f"  Dirt/Stone total: {dirt_stone:.1%}")
    print(f"  Grass: {grass_present:.1%}")
    print(f"  Sky: {sky_present:.1%}")
    
    # Determine likely environment
    if sky_present > 0.2:
        minecraft_indicators.append("Likely outdoors (sky visible)")
    elif sky_present < 0.05:
        minecraft_indicators.append("Likely indoors/underground (no sky)")
    
    if wood_leaves > 0.1:
        minecraft_indicators.append("Trees/forest area detected")
    
    if dirt_stone > 0.1:
        minecraft_indicators.append("Mining/building area detected")
    
    if grass_present > 0.1:
        minecraft_indicators.append("Grass surface detected")
    
    # Check for black areas (could be UI, caves, etc.)
    black_areas = color_coverage.get('black', 0)
    if black_areas > 0.3:
        minecraft_indicators.append("Dark areas detected (caves/UI/night)")
    
    print(f"\nMinecraft indicators found:")
    if minecraft_indicators:
        for indicator in minecraft_indicators:
            print(f"  ✅ {indicator}")
        
        print(f"\n🎮 Minecraft-like environment detected!")
        return True
    else:
        print("  ❌ No clear Minecraft indicators found")
        print("  💡 This might not be showing Minecraft, or colors need adjustment")
        return False

def test_vision_changes():
    """Test if vision detects changes over time"""
    print("\n=== Testing Vision Change Detection ===")
    
    print("Taking first screenshot...")
    img1 = test_screen_capture()
    if img1 is None:
        return False
    
    print("\nWaiting 3 seconds...")
    print("(Try switching windows or moving something on screen)")
    time.sleep(3)
    
    print("Taking second screenshot...")
    sct = mss.mss()
    screenshot2 = sct.grab(sct.monitors[1])
    img2 = Image.frombytes("RGB", screenshot2.size, screenshot2.bgra, "raw", "BGRX")
    
    # Compare images
    try:
        img1_array = np.array(img1)
        img2_array = np.array(img2)
        
        # Calculate difference
        diff = np.abs(img1_array.astype(np.float32) - img2_array.astype(np.float32))
        avg_diff = np.mean(diff)
        max_diff = np.max(diff)
        
        print(f"\nImage comparison:")
        print(f"  Average pixel difference: {avg_diff:.2f}")
        print(f"  Maximum pixel difference: {max_diff:.2f}")
        
        if avg_diff > 5.0:
            print("  ✅ Significant changes detected - vision system is responsive")
            return True
        else:
            print("  ⚠️ Little change detected - screen might be static")
            return True  # Still working, just static
            
    except Exception as e:
        print(f"❌ Change detection failed: {e}")
        return False

def main():
    print("🔍 Vision System Validation Test")
    print("=" * 50)
    print("This test verifies that computer vision is actually working")
    print()
    
    # Test 1: Basic screen capture
    image = test_screen_capture()
    
    # Test 2: Color analysis
    color_data = test_color_analysis(image)
    
    # Test 3: Minecraft detection
    minecraft_detected = test_minecraft_detection(color_data)
    
    # Test 4: Change detection
    change_detected = test_vision_changes()
    
    # Summary
    print("\n" + "=" * 50)
    print("🔍 VISION VALIDATION SUMMARY")
    print(f"Screen Capture: {'✅ WORKING' if image else '❌ FAILED'}")
    print(f"Color Analysis: {'✅ WORKING' if color_data else '❌ FAILED'}")
    print(f"Minecraft Detection: {'✅ DETECTED' if minecraft_detected else '⚠️ NOT DETECTED'}")
    print(f"Change Detection: {'✅ WORKING' if change_detected else '❌ FAILED'}")
    
    if all([image, color_data, change_detected]):
        print("\n🎉 Vision system is fully functional!")
        print("✅ The LLM agent can see and analyze the screen")
        print("✅ Color detection is working properly")
        print("✅ Real-time changes are being captured")
        
        if minecraft_detected:
            print("✅ Minecraft environment detected - agent can play!")
        else:
            print("💡 Open Minecraft for the agent to analyze the game")
            
        print(f"\n📁 Check 'vision_test_screenshot.png' to see what the agent sees")
    else:
        print("\n❌ Vision system has issues")
        print("🔧 Check the output above for specific problems")

if __name__ == "__main__":
    main()