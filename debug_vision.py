#!/usr/bin/env python3
"""
Debug version that shows what the agent sees in real-time
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minecraft_ai.core.config import Config
from minecraft_ai.vision.screen_capture import create_screen_capture, MinecraftVision


def debug_agent_vision():
    """Debug what the agent sees"""
    print("🔍 Debug: Agent Vision Analysis")
    print("===============================\n")
    
    # Load config
    config = Config("config/iphone_mirroring.yaml")
    
    # Create vision system
    screen_capture = create_screen_capture('mss')
    vision = MinecraftVision(
        screen_capture,
        image_scale=config.get('vision.image_scale', 0.5),
        color_space=config.get('vision.color_space', 'RGB')
    )
    
    # Get screen region from config
    screen_region = config.get('vision.screen_region')
    print(f"📱 Using screen region: {screen_region}")
    
    # Analyze 5 frames to see what agent sees
    for i in range(5):
        print(f"\n--- Frame {i+1} ---")
        
        # Get analysis (same as agent does)
        analysis = vision.analyze_environment(screen_region)
        
        print(f"📊 Analysis results:")
        print(f"   Image shape: {analysis['image_shape']}")
        print(f"   Color coverage:")
        
        total_coverage = 0
        for color, coverage in analysis['color_coverage'].items():
            percentage = coverage * 100
            total_coverage += coverage
            print(f"     {color}: {percentage:.2f}%")
        
        print(f"   Total coverage: {total_coverage*100:.2f}%")
        
        # Save frame for inspection
        image = vision.get_current_view(screen_region)
        vision.processor.save_image(image, f"logs/debug_frame_{i+1}.png")
        print(f"   💾 Frame saved to: logs/debug_frame_{i+1}.png")
        
        # Simulate agent decision logic
        if total_coverage > 0.3:  # 30% threshold
            if analysis['color_coverage'].get('grass', 0) > 0.3:
                decision = "move_forward (lots of grass)"
            elif analysis['color_coverage'].get('water', 0) > 0.1:
                decision = "turn_right (water detected)"
            elif analysis['color_coverage'].get('stone', 0) > 0.2:
                decision = "mine (stone detected)"
            else:
                decision = "look_around (mixed content)"
        else:
            decision = "look_around (low content)"
        
        print(f"   🤖 Agent would decide: {decision}")
        
        time.sleep(1)  # Wait 1 second between frames


if __name__ == "__main__":
    debug_agent_vision()