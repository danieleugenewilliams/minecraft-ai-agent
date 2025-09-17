#!/usr/bin/env python3
"""
Screen analysis utility to help find the iPhone mirroring window
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minecraft_ai.vision.screen_capture import create_screen_capture, ImageProcessor
import numpy as np


def analyze_full_screen():
    """Capture and analyze the full screen to help locate iPhone mirroring"""
    print("📱 Analyzing screen to find iPhone mirroring window...")
    
    # Create screen capture
    screen_capture = create_screen_capture('mss')
    processor = ImageProcessor()
    
    # Get monitor info
    monitor_info = screen_capture.get_monitor_info()
    print(f"Monitor: {monitor_info['width']}x{monitor_info['height']} at ({monitor_info['left']}, {monitor_info['top']})")
    
    # Capture full screen
    print("📸 Capturing full screen...")
    full_image = screen_capture.capture()
    
    # Save screenshot for reference
    screenshot_path = "logs/full_screen_capture.png"
    processor.save_image(full_image, screenshot_path)
    print(f"💾 Full screenshot saved to: {screenshot_path}")
    
    # Analyze image
    height, width = full_image.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    
    # Look for regions that might be iPhone-shaped (tall rectangles)
    # iPhone aspect ratio is roughly 19.5:9 or about 2.17:1
    print("\n🔍 Looking for iPhone-shaped regions...")
    
    # Convert to grayscale for edge detection
    gray = processor.convert_color_space(full_image, 'GRAY')
    
    # Simple analysis: look for dark rectangular regions that could be iPhone bezels
    # This is a basic heuristic - in practice you'd want more sophisticated detection
    
    # Suggest some common locations for iPhone mirroring
    suggested_regions = [
        # Bottom center (common placement)
        {"left": width//4, "top": height//2, "width": width//2, "height": height//2},
        # Bottom right
        {"left": width//2, "top": height//2, "width": width//2, "height": height//2},
        # Bottom left  
        {"left": 0, "top": height//2, "width": width//2, "height": height//2},
        # Center
        {"left": width//4, "top": height//4, "width": width//2, "height": height//2},
    ]
    
    print("\n📋 Suggested regions to test (you mentioned iPhone is at bottom):")
    for i, region in enumerate(suggested_regions):
        print(f"  Region {i+1}: x={region['left']}, y={region['top']}, w={region['width']}, h={region['height']}")
        
        # Test capture this region
        test_image = screen_capture.capture(region)
        region_path = f"logs/test_region_{i+1}.png"
        processor.save_image(test_image, region_path)
        print(f"    Sample saved to: {region_path}")
    
    return suggested_regions


def test_minecraft_detection(region=None):
    """Test Minecraft color detection in a specific region"""
    print(f"\n🎮 Testing Minecraft detection in region: {region}")
    
    from minecraft_ai.vision.screen_capture import MinecraftVision
    
    screen_capture = create_screen_capture('mss')
    vision = MinecraftVision(screen_capture, image_scale=1.0)  # Full scale for testing
    
    # Analyze the region
    analysis = vision.analyze_environment(region)
    
    print("🔍 Analysis results:")
    print(f"  Image shape: {analysis['image_shape']}")
    print(f"  Color coverage:")
    for color, coverage in analysis['color_coverage'].items():
        percentage = coverage * 100
        print(f"    {color}: {percentage:.2f}%")
    
    # Save analyzed image
    image = vision.get_current_view(region)
    vision.processor.save_image(image, "logs/minecraft_analysis.png")
    print("💾 Analysis image saved to: logs/minecraft_analysis.png")
    
    return analysis


def main():
    """Main function"""
    print("🎯 Minecraft AI - Screen Analysis Tool")
    print("=====================================\n")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # First, analyze full screen
    suggested_regions = analyze_full_screen()
    
    print(f"\n⏰ Waiting 3 seconds for you to position your iPhone mirroring window...")
    time.sleep(3)
    
    # Test each suggested region
    print("\n🧪 Testing Minecraft detection in suggested regions...")
    for i, region in enumerate(suggested_regions):
        print(f"\n--- Testing Region {i+1} ---")
        analysis = test_minecraft_detection(region)
        
        # Check if this looks like Minecraft (any significant color coverage)
        total_coverage = sum(analysis['color_coverage'].values())
        if total_coverage > 0.05:  # 5% threshold
            print(f"✅ Region {i+1} might contain Minecraft content!")
            print(f"   Total color coverage: {total_coverage*100:.1f}%")
        else:
            print(f"❌ Region {i+1} appears to be mostly background")
    
    print(f"\n💡 Tips:")
    print(f"   1. Check the saved screenshots in the logs/ folder")
    print(f"   2. Look for the region that contains your iPhone mirroring")
    print(f"   3. You can manually specify coordinates in the config file")
    print(f"   4. iPhone mirroring usually appears as a tall rectangle")


if __name__ == "__main__":
    main()