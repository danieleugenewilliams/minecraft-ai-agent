#!/usr/bin/env python3
"""
Vision-Enabled LLM Minecraft Agent
Combines computer vision with LLM reasoning for intelligent Minecraft gameplay
"""

import requests
import time
import subprocess
import sys
import pyautogui
import mss
import numpy as np
from PIL import Image
import io

class MinecraftVision:
    """Computer vision system for analyzing Minecraft screenshots"""
    
    def __init__(self):
        self.sct = mss.mss()
        
        # Minecraft color ranges (BGR format for easier comparison)
        self.color_ranges = {
            'wood': [(101, 67, 33), (160, 130, 80)],      # Brown wood colors
            'leaves': [(20, 70, 20), (80, 150, 80)],      # Green leaf colors
            'dirt': [(101, 67, 33), (139, 90, 60)],       # Brown dirt colors
            'stone': [(100, 100, 100), (180, 180, 180)],  # Gray stone colors
            'grass': [(40, 100, 40), (100, 180, 100)],    # Green grass colors
            'sky': [(200, 150, 100), (255, 220, 180)],    # Blue/light blue sky
            'water': [(150, 100, 50), (255, 180, 120)],   # Blue water
        }
    
    def capture_screen(self):
        """Capture the current screen"""
        try:
            # Capture the primary monitor
            monitor = self.sct.monitors[1]
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            return img
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def analyze_colors(self, image):
        """Analyze color composition of the image"""
        if image is None:
            return {}
        
        # Convert to numpy array
        img_array = np.array(image)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        color_coverage = {}
        
        for color_name, (lower, upper) in self.color_ranges.items():
            # Create mask for this color range
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            color_pixels = np.sum(mask)
            coverage = color_pixels / total_pixels
            color_coverage[color_name] = coverage
        
        return color_coverage
    
    def get_visual_summary(self):
        """Get a summary of what's currently visible"""
        image = self.capture_screen()
        if image is None:
            return {"error": "Could not capture screen"}
        
        color_coverage = self.analyze_colors(image)
        
        # Create visual summary
        visual_summary = {
            "resolution": f"{image.width}x{image.height}",
            "color_coverage": color_coverage,
            "dominant_colors": sorted(color_coverage.items(), key=lambda x: x[1], reverse=True)[:3],
            "has_screenshot": True
        }
        
        # Add interpretation
        wood_visible = color_coverage.get('wood', 0) + color_coverage.get('leaves', 0)
        dirt_visible = color_coverage.get('dirt', 0) + color_coverage.get('stone', 0)
        
        visual_summary["interpretation"] = {
            "trees_nearby": wood_visible > 0.1,
            "mining_area": dirt_visible > 0.15,
            "open_area": color_coverage.get('sky', 0) > 0.3,
            "underground": color_coverage.get('sky', 0) < 0.1
        }
        
        return visual_summary

class VisionLLMAgent:
    """LLM agent with computer vision capabilities"""
    
    def __init__(self):
        self.objective = "Build a small shelter by gathering wood and dirt"
        self.action_count = 0
        self.last_actions = []
        self.vision = MinecraftVision()
        
        # Configure pyautogui for safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
    
    def focus_minecraft(self):
        """Focus iPhone Mirroring window"""
        try:
            script = '''
            tell application "System Events"
                try
                    set targetApp to first application process whose name is "iPhone Mirroring"
                    set frontmost of targetApp to true
                    return "focused"
                on error
                    return "not found"
                end try
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "focused" in result.stdout:
                print("✓ Focused iPhone Mirroring")
                time.sleep(0.5)
                return True
            else:
                print("⚠ Could not focus iPhone Mirroring")
                return False
        except Exception as e:
            print(f"Error focusing: {e}")
            return False
    
    def analyze_environment(self):
        """Analyze the current visual environment"""
        print("👀 Analyzing environment...")
        visual_data = self.vision.get_visual_summary()
        
        if "error" in visual_data:
            print(f"Vision error: {visual_data['error']}")
            return None
        
        return visual_data
    
    def make_decision(self, visual_data):
        """Use LLM to make decision based on visual analysis"""
        system_prompt = """You are an AI controlling a Minecraft character through iPhone mirroring with computer vision. 

OBJECTIVE: Build a small shelter by gathering wood and dirt

CONTROLS:
- move_forward: UP arrow (ONLY movement that works!)
- look_left: j key to turn camera left
- look_right: l key to turn camera right  
- look_up: i key to look up
- look_down: k key to look down
- center_view: enter key to center camera
- mine: left click to break blocks
- wait: do nothing for one cycle

STRATEGY:
1. Use visual data to identify resources (wood/leaves = trees, dirt/stone = mining areas)
2. Move toward resource-rich areas
3. Mine blocks when close to trees or dirt
4. Gather materials systematically
5. Look around to scan for new resource areas

Respond with exactly: ACTION: [action_name]
REASON: [brief explanation based on what you see]"""
        
        recent_actions_str = ", ".join(self.last_actions[-3:]) if self.last_actions else "none"
        
        # Create detailed visual description
        if visual_data:
            color_coverage = visual_data.get('color_coverage', {})
            interpretation = visual_data.get('interpretation', {})
            
            visual_description = f"""VISUAL ANALYSIS:
Screen resolution: {visual_data.get('resolution', 'unknown')}

Color Coverage:
- Wood/Trees: {color_coverage.get('wood', 0):.1%} wood + {color_coverage.get('leaves', 0):.1%} leaves = {(color_coverage.get('wood', 0) + color_coverage.get('leaves', 0)):.1%} total
- Dirt/Stone: {color_coverage.get('dirt', 0):.1%} dirt + {color_coverage.get('stone', 0):.1%} stone = {(color_coverage.get('dirt', 0) + color_coverage.get('stone', 0)):.1%} total  
- Grass: {color_coverage.get('grass', 0):.1%}
- Sky: {color_coverage.get('sky', 0):.1%}
- Water: {color_coverage.get('water', 0):.1%}

Environment Assessment:
- Trees nearby: {"YES" if interpretation.get('trees_nearby') else "NO"}
- Mining area: {"YES" if interpretation.get('mining_area') else "NO"}
- Open area: {"YES" if interpretation.get('open_area') else "NO"}
- Underground: {"YES" if interpretation.get('underground') else "NO"}"""
        else:
            visual_description = "VISUAL ANALYSIS: No visual data available"
        
        user_prompt = f"""Current state:
- Action #{self.action_count + 1}
- Recent actions: {recent_actions_str}
- Objective: Find and gather wood/dirt for shelter

{visual_description}

Based on what you can see, what should you do next? 
- If you see trees (wood/leaves), move toward them or mine them
- If you see dirt/stone areas, move toward them for foundation materials
- If mostly sky visible, look around to find resources
- If underground, look for minerals and dirt
- Use move_forward to approach resources, looking actions to scan

Choose your next action:"""
        
        try:
            payload = {
                "model": "qwen2.5:7b",
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "").strip()
                
                print(f"🧠 LLM thinking: {llm_response[:100]}...")
                
                # Parse action and reason
                action = None
                reason = None
                
                for line in llm_response.split('\n'):
                    line = line.strip()
                    if line.startswith('ACTION:'):
                        action = line.replace('ACTION:', '').strip()
                    elif line.startswith('REASON:'):
                        reason = line.replace('REASON:', '').strip()
                
                if action:
                    print(f"💡 Reason: {reason or 'Strategic decision'}")
                    return action
                else:
                    return "look_right"  # Fallback
            else:
                print(f"LLM error: {response.status_code}")
                return "wait"
                
        except Exception as e:
            print(f"LLM error: {e}")
            return "wait"
    
    def execute_action(self, action):
        """Execute action using real controls"""
        print(f"🎮 Executing: {action}")
        
        try:
            if action == 'move_forward':
                pyautogui.keyDown('up')
                time.sleep(0.8)  # Move for 0.8 seconds
                pyautogui.keyUp('up')
                
            elif action == 'look_left':
                pyautogui.keyDown('j')
                time.sleep(0.4)  # Look for 0.4 seconds
                pyautogui.keyUp('j')
                
            elif action == 'look_right':
                pyautogui.keyDown('l')
                time.sleep(0.4)
                pyautogui.keyUp('l')
                
            elif action == 'look_up':
                pyautogui.keyDown('i')
                time.sleep(0.3)
                pyautogui.keyUp('i')
                
            elif action == 'look_down':
                pyautogui.keyDown('k')
                time.sleep(0.3)
                pyautogui.keyUp('k')
                
            elif action == 'center_view':
                pyautogui.press('enter')
                
            elif action == 'mine':
                # Click and hold for mining
                pyautogui.mouseDown()
                time.sleep(0.8)  # Mine for longer
                pyautogui.mouseUp()
                
            elif action == 'wait':
                time.sleep(1.0)
                
            else:
                print(f"Unknown action: {action}")
                time.sleep(0.5)
            
            # Record action
            self.last_actions.append(action)
            if len(self.last_actions) > 10:
                self.last_actions = self.last_actions[-10:]
            
            return True
            
        except Exception as e:
            print(f"Error executing {action}: {e}")
            return False
    
    def run_cycle(self):
        """Run one complete agent cycle with vision"""
        print(f"\n🤖 Vision Agent Cycle {self.action_count + 1}")
        print("-" * 40)
        
        # Focus Minecraft
        if not self.focus_minecraft():
            print("⚠ Could not focus Minecraft, but continuing...")
        
        # Analyze environment with vision
        visual_data = self.analyze_environment()
        
        if visual_data and isinstance(visual_data, dict):
            # Show key visual info
            interpretation = visual_data.get('interpretation', {})
            color_coverage = visual_data.get('color_coverage', {})
            
            if isinstance(color_coverage, dict) and isinstance(interpretation, dict):
                wood_total = color_coverage.get('wood', 0) + color_coverage.get('leaves', 0)
                dirt_total = color_coverage.get('dirt', 0) + color_coverage.get('stone', 0)
                
                print(f"🌳 Trees: {wood_total:.1%} | 🪨 Dirt/Stone: {dirt_total:.1%} | 🌤️ Sky: {color_coverage.get('sky', 0):.1%}")
                print(f"📍 Environment: {'Trees nearby' if interpretation.get('trees_nearby') else 'No trees'}, {'Open area' if interpretation.get('open_area') else 'Enclosed area'}")
            else:
                print("📊 Visual data format error")
        else:
            print("👁️ No visual data available")
        
        # Make decision based on vision
        action = self.make_decision(visual_data)
        print(f"⚡ Decision: {action}")
        
        # Execute action
        success = self.execute_action(action)
        
        self.action_count += 1
        
        if not success:
            print("❌ Action failed")
        
        return success

def main():
    print("🎮👁️ Vision-Enabled LLM Minecraft Agent")
    print("=" * 50)
    print("This agent uses computer vision + LLM reasoning!")
    print("Prerequisites:")
    print("  1. iPhone Mirroring is running")
    print("  2. Minecraft is open and visible")
    print("  3. Character can move around")
    print()
    
    # Auto-start with 8 cycles for more interesting behavior
    max_cycles = 8
    
    print(f"Starting vision agent with {max_cycles} cycles...")
    print("The agent will:")
    print("  - Analyze what's visible on screen")
    print("  - Make intelligent decisions based on visual data")
    print("  - Look for trees, dirt, and resources")
    print("  - Move toward resource-rich areas")
    print()
    print("Press Ctrl+C to stop early")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Create and run vision agent
    agent = VisionLLMAgent()
    successful_cycles = 0
    
    try:
        for i in range(max_cycles):
            success = agent.run_cycle()
            if success:
                successful_cycles += 1
            
            # Pause between cycles
            time.sleep(2.0)  # Longer pause for vision processing
            
            # Check for user interrupt
            print("(Press Ctrl+C to stop)")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Vision agent stopped by user")
    except Exception as e:
        print(f"\n\n❌ Vision agent error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 VISION AGENT SESSION COMPLETE")
    print(f"Total cycles: {agent.action_count}")
    print(f"Successful cycles: {successful_cycles}")
    print(f"Success rate: {successful_cycles/max(agent.action_count,1)*100:.1f}%")
    print(f"Actions taken: {', '.join(agent.last_actions[-5:])}")
    print(f"Objective: {agent.objective}")
    print("\nDid the agent use vision to find and gather resources? 👀🏗️")

if __name__ == "__main__":
    main()