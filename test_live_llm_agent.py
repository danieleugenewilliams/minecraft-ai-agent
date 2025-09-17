#!/usr/bin/env python3
"""
Live LLM Minecraft Agent Test
Actually controls Minecraft through iPhone Mirroring
"""

import requests
import time
import subprocess
import sys
import pyautogui

class LiveLLMAgent:
    """Live LLM agent that actually controls Minecraft"""
    
    def __init__(self):
        self.objective = "Build a small shelter by gathering wood and dirt"
        self.action_count = 0
        self.last_actions = []
        
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
    
    def make_decision(self):
        """Use LLM to make decision based on current state"""
        system_prompt = """You are controlling a Minecraft character through iPhone mirroring. 

OBJECTIVE: Build a small shelter by gathering wood and dirt

CRITICAL CONTROLS:
- move_forward: UP arrow (ONLY movement that works!)
- look_left: j key to turn camera left
- look_right: l key to turn camera right  
- look_up: i key to look up
- look_down: k key to look down
- center_view: enter key to center camera
- mine: left click to break blocks
- wait: do nothing for one cycle

STRATEGY:
1. Look around to find trees (wood/leaves)
2. Move toward trees using move_forward
3. Mine wood blocks
4. Find dirt areas
5. Gather materials for shelter

Respond with exactly: ACTION: [action_name]"""
        
        recent_actions_str = ", ".join(self.last_actions[-3:]) if self.last_actions else "none"
        
        user_prompt = f"""Current state:
- Action #{self.action_count + 1}
- Recent actions: {recent_actions_str}
- Objective: Find and gather wood/dirt for shelter

What should you do next? Be strategic about exploring and resource gathering.
Remember: ONLY move_forward works for movement, use looking to scan for resources."""
        
        try:
            payload = {
                "model": "qwen2.5:7b",
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": 0.4}
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "").strip()
                
                print(f"LLM thinking: {llm_response[:80]}...")
                
                # Parse action
                for line in llm_response.split('\n'):
                    if line.strip().startswith('ACTION:'):
                        action = line.replace('ACTION:', '').strip()
                        return action
                
                # Fallback to looking around
                return "look_right"
            else:
                print(f"LLM error: {response.status_code}")
                return "wait"
                
        except Exception as e:
            print(f"LLM error: {e}")
            return "wait"
    
    def execute_action(self, action):
        """Execute action using real controls"""
        print(f"Executing: {action}")
        
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
                time.sleep(0.5)
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
        """Run one complete agent cycle"""
        print(f"\n🤖 Agent Cycle {self.action_count + 1}")
        print("-" * 30)
        
        # Focus Minecraft
        if not self.focus_minecraft():
            print("⚠ Could not focus Minecraft, but continuing...")
        
        # Make decision
        action = self.make_decision()
        print(f"Decision: {action}")
        
        # Execute action
        success = self.execute_action(action)
        
        self.action_count += 1
        
        if not success:
            print("❌ Action failed")
        
        return success

def main():
    print("🎮 Live LLM Minecraft Agent")
    print("=" * 40)
    print("This agent will automatically control Minecraft!")
    print("Prerequisites:")
    print("  1. iPhone Mirroring is running")
    print("  2. Minecraft is open and visible")
    print("  3. Character can move around")
    print()
    
    # Auto-start with 5 cycles
    max_cycles = 5
    
    print(f"Starting agent with {max_cycles} cycles...")
    print("Press Ctrl+C to stop early")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Create and run agent
    agent = LiveLLMAgent()
    successful_cycles = 0
    
    try:
        for i in range(max_cycles):
            success = agent.run_cycle()
            if success:
                successful_cycles += 1
            
            # Pause between cycles
            time.sleep(1.5)
            
            # Check for user interrupt
            print("(Press Ctrl+C to stop)")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Agent stopped by user")
    except Exception as e:
        print(f"\n\n❌ Agent error: {e}")
    
    # Summary
    print("\n" + "=" * 40)
    print("🏁 AGENT SESSION COMPLETE")
    print(f"Total cycles: {agent.action_count}")
    print(f"Successful cycles: {successful_cycles}")
    print(f"Success rate: {successful_cycles/max(agent.action_count,1)*100:.1f}%")
    print(f"Actions taken: {', '.join(agent.last_actions[-5:])}")
    print(f"Objective: {agent.objective}")
    print("\nDid the agent explore and try to gather resources? 🏗️")

if __name__ == "__main__":
    main()