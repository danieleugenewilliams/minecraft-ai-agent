#!/usr/bin/env python3
"""
Test script for LLM Minecraft Agent
Tests vision system, input controls, and LLM decision making
"""

import sys
import os
import time
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minecraft_ai.ai.llm_agent import LLMMinecraftAgent
from minecraft_ai.automation.input_controller import MacOSInputController, DryRunInputController
from minecraft_ai.vision.screen_capture import MinecraftVision

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vision_system():
    """Test the vision system independently"""
    print("=== Testing Vision System ===")
    
    try:
        vision = MinecraftVision(screen_capture=None)  # Will create default
        
        # Take a screenshot and analyze
        env_analysis = vision.analyze_environment()
        
        print("Environment Analysis:")
        print(f"- Resolution: {env_analysis.get('resolution', 'Unknown')}")
        print(f"- Has Screenshot: {env_analysis.get('has_screenshot', False)}")
        
        color_coverage = env_analysis.get('color_coverage', {})
        print("Color Coverage:")
        for color, percentage in color_coverage.items():
            print(f"  - {color}: {percentage:.1%}")
        
        return env_analysis
    
    except Exception as e:
        print(f"Vision test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_input_controls():
    """Test input controls in dry run mode"""
    print("\n=== Testing Input Controls (Dry Run) ===")
    
    try:
        # Create dry run controller to test without actually controlling
        controller = DryRunInputController()
        
        # Test basic movements
        print("Testing movement controls:")
        controller.key_press('up')
        time.sleep(0.1)
        controller.key_release('up')
        
        print("Testing camera controls:")
        controller.key_press('j')  # Look left
        time.sleep(0.1)
        controller.key_release('j')
        
        controller.key_press('l')  # Look right
        time.sleep(0.1)
        controller.key_release('l')
        
        print("Testing center view:")
        controller.center_view()
        
        print("Testing mouse controls:")
        controller.click(640, 360, 'left')  # Mine
        controller.click(640, 360, 'right')  # Place
        
        print("All input tests completed!")
        return controller.get_actions()
    
    except Exception as e:
        print(f"Input control test failed: {e}")
        return None

def test_llm_agent_dry_run():
    """Test LLM agent in dry run mode (no actual input)"""
    print("\n=== Testing LLM Agent (Dry Run) ===")
    
    try:
        # Create components
        vision = MinecraftVision()
        controller = DryRunInputController()
        agent = LLMMinecraftAgent(controller, vision)
        
        print("Agent created successfully!")
        print(f"Objective: {agent.objective}")
        
        # Test observation
        print("\nTesting observation...")
        observation = agent.observe()
        
        if 'error' in observation:
            print(f"Observation error: {observation['error']}")
            return False
        
        print(f"Observation successful. Colors detected: {len(observation.get('color_coverage', {}))}")
        
        # Test decision making
        print("\nTesting LLM decision making...")
        action = agent.decide(observation)
        
        if action:
            print(f"LLM Decision: {action}")
            
            # Test action execution
            print("\nTesting action execution...")
            success = agent.act(action)
            print(f"Action execution: {'Success' if success else 'Failed'}")
            
            # Show what actions were recorded
            print("\nRecorded actions:")
            for recorded_action in controller.get_actions():
                print(f"  - {recorded_action}")
        else:
            print("No action decided by LLM")
            return False
        
        return True
    
    except Exception as e:
        print(f"LLM agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_agent_live():
    """Test LLM agent with real controls (CAREFUL!)"""
    print("\n=== Testing LLM Agent (LIVE - Real Controls) ===")
    print("WARNING: This will actually control your computer!")
    print("Make sure Minecraft is running and iPhone Mirroring is active.")
    
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Live test cancelled.")
        return False
    
    try:
        # Create components with real controls
        vision = MinecraftVision()
        controller = MacOSInputController()
        agent = LLMMinecraftAgent(controller, vision)
        
        print("Starting live agent test...")
        print("Agent will take ONE action then stop.")
        
        # Give time to switch to Minecraft
        print("Switching to Minecraft in 3 seconds...")
        time.sleep(3)
        
        # Run one cycle
        observation = agent.observe()
        if 'error' in observation:
            print(f"Observation failed: {observation['error']}")
            return False
        
        print(f"Environment observed. Sky: {observation['color_coverage'].get('sky', 0):.1%}")
        
        action = agent.decide(observation)
        if action:
            print(f"Action decided: {action}")
            success = agent.act(action)
            print(f"Action executed: {'Success' if success else 'Failed'}")
        else:
            print("No action decided")
        
        return True
    
    except Exception as e:
        print(f"Live agent test failed: {e}")
        return False

if __name__ == "__main__":
    print("Minecraft AI LLM Agent Test Suite")
    print("=" * 50)
    
    # Test vision system
    vision_result = test_vision_system()
    
    # Test input controls
    input_result = test_input_controls()
    
    # Test LLM agent in dry run mode
    dry_run_result = test_llm_agent_dry_run()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Vision System: {'✓ PASS' if vision_result else '✗ FAIL'}")
    print(f"Input Controls: {'✓ PASS' if input_result else '✗ FAIL'}")
    print(f"LLM Agent (Dry Run): {'✓ PASS' if dry_run_result else '✗ FAIL'}")
    
    if all([vision_result, input_result, dry_run_result]):
        print("\n🎉 All tests passed! LLM agent is ready.")
        
        # Offer to run live test
        print("\nOptional: Test with real controls?")
        live_result = test_llm_agent_live()
        if live_result:
            print("✓ Live test also passed!")
    else:
        print("\n❌ Some tests failed. Check the output above.")