#!/usr/bin/env python3
"""
Test script for Minecraft AI foundational systems
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minecraft_ai.core.config import Config
from minecraft_ai.vision.screen_capture import create_screen_capture, MinecraftVision
from minecraft_ai.automation.input_controller import create_input_controller

def test_vision_system():
    """Test screen capture and vision analysis"""
    print("🔍 Testing vision system...")
    
    try:
        # Create screen capture
        screen_capture = create_screen_capture('mss')
        vision = MinecraftVision(screen_capture, image_scale=0.5)
        
        # Test basic screen capture
        image = vision.get_current_view()
        print(f"✅ Screen capture successful: {image.shape}")
        
        # Test environment analysis
        analysis = vision.analyze_environment()
        print(f"✅ Environment analysis successful:")
        print(f"   Image shape: {analysis['image_shape']}")
        print(f"   Color coverage: {analysis['color_coverage']}")
        
        # Save a test screenshot
        from minecraft_ai.vision.screen_capture import ImageProcessor
        ImageProcessor.save_image(image, "test_screenshot.png")
        print("✅ Screenshot saved as test_screenshot.png")
        
        return True
        
    except Exception as e:
        print(f"❌ Vision system error: {e}")
        return False

def test_input_system(dry_run=True):
    """Test input controller system"""
    print(f"🎮 Testing input system (dry_run={dry_run})...")
    
    try:
        # Create input controller
        controller = create_input_controller(dry_run=dry_run)
        
        if dry_run:
            print("🔥 DRY RUN MODE - No actual input will be sent")
        
        # Test basic controls
        print("Testing movement controls...")
        controller.key_press('w')
        time.sleep(0.1)
        controller.key_release('w')
        print("✅ Forward movement test")
        
        controller.key_press('a')
        time.sleep(0.1)
        controller.key_release('a')
        print("✅ Left movement test")
        
        # Test mouse controls
        print("Testing mouse controls...")
        if hasattr(controller, 'get_mouse_position'):
            pos = controller.get_mouse_position()
            print(f"✅ Mouse position: {pos}")
            
            # Small mouse movement
            controller.move_mouse(pos[0] + 10, pos[1])
            print("✅ Mouse movement test")
        
        # Test click
        controller.click(500, 500, 'left')
        print("✅ Mouse click test")
        
        return True
        
    except Exception as e:
        print(f"❌ Input system error: {e}")
        return False

def test_agent_observation():
    """Test agent observation cycle"""
    print("🤖 Testing agent observation cycle...")
    
    try:
        # Load config
        config = Config()
        
        # Create components
        screen_capture = create_screen_capture('mss')
        vision = MinecraftVision(screen_capture, image_scale=0.5)
        controller = create_input_controller(dry_run=True)  # Safe dry run
        
        # Test observation
        print("Running observation cycle...")
        observation = vision.analyze_environment()
        
        print("✅ Observation successful:")
        for color, coverage in observation['color_coverage'].items():
            percentage = coverage * 100
            print(f"   {color}: {percentage:.2f}% coverage")
        
        # Simple decision logic test
        color_coverage = observation.get('color_coverage', {})
        if color_coverage.get('grass', 0) > 0.1:
            print("🌱 Detected significant grass - would move forward")
        elif color_coverage.get('stone', 0) > 0.05:
            print("🪨 Detected stone - would attempt mining")
        else:
            print("👀 No clear targets - would look around")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent observation error: {e}")
        return False

def main():
    """Run all foundation tests"""
    print("🚀 Starting Minecraft AI Foundation Tests\n")
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Vision System", test_vision_system),
        ("Input System (Dry Run)", lambda: test_input_system(dry_run=True)),
        ("Agent Observation", test_agent_observation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All foundation tests passed! Ready for Minecraft testing.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()