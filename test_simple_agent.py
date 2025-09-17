#!/usr/bin/env python3
"""
Simple LLM Minecraft Agent for testing
"""

import requests
import time
import subprocess
import sys
import os

class SimpleLLMAgent:
    """Simplified LLM agent for integration testing"""
    
    def __init__(self):
        self.objective = "Build a small shelter by gathering wood and dirt"
        self.action_count = 0
        
    def get_vision_data(self):
        """Get vision data by running existing vision test"""
        try:
            result = subprocess.run([
                sys.executable, 'test_minecraft_vision.py'
            ], capture_output=True, text=True, timeout=5)
            
            # Parse basic info from output
            vision_data = {
                'has_screenshot': 'resolution' in result.stdout.lower(),
                'can_analyze': 'color' in result.stdout.lower(),
                'status': 'working' if result.returncode == 0 else 'error'
            }
            return vision_data
        except:
            return {'status': 'error'}
    
    def make_decision(self, vision_data):
        """Use LLM to make decision"""
        system_prompt = """You are controlling a Minecraft character. 
        
        OBJECTIVE: Build a shelter by gathering wood and dirt
        
        CONTROLS THAT WORK:
        - move_forward: UP arrow (ONLY movement that works)
        - look_left: j key
        - look_right: l key  
        - look_up: i key
        - look_down: k key
        - center_view: enter key
        - mine: left click
        
        Respond with: ACTION: [action_name]"""
        
        user_prompt = f"""Vision status: {vision_data.get('status', 'unknown')}
        Action number: {self.action_count + 1}
        
        What should you do next? Choose ONE action."""
        
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
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "").strip()
                
                # Parse action
                for line in llm_response.split('\n'):
                    if line.strip().startswith('ACTION:'):
                        action = line.replace('ACTION:', '').strip()
                        return action
                
                # Fallback
                return "look_around"
            else:
                return "wait"
                
        except Exception as e:
            print(f"LLM error: {e}")
            return "wait"
    
    def execute_action(self, action):
        """Execute action using input system"""
        print(f"Executing action: {action}")
        
        # For now, just simulate execution
        # In real implementation, this would use the input controller
        simulated_actions = {
            'move_forward': 'Press UP arrow',
            'look_left': 'Press j key',
            'look_right': 'Press l key',
            'look_up': 'Press i key',
            'look_down': 'Press k key',
            'center_view': 'Press enter key',
            'mine': 'Left click',
            'wait': 'Sleep 0.5s'
        }
        
        action_desc = simulated_actions.get(action, 'Unknown action')
        print(f"  -> {action_desc}")
        
        # Small delay to simulate action
        time.sleep(0.1)
        return True
    
    def run_one_cycle(self):
        """Run one complete agent cycle"""
        print(f"\n--- Agent Cycle {self.action_count + 1} ---")
        
        # 1. Get vision data
        print("1. Getting vision data...")
        vision_data = self.get_vision_data()
        print(f"   Vision status: {vision_data.get('status', 'unknown')}")
        
        # 2. Make decision
        print("2. Making LLM decision...")
        action = self.make_decision(vision_data)
        print(f"   Decided action: {action}")
        
        # 3. Execute action
        print("3. Executing action...")
        success = self.execute_action(action)
        
        self.action_count += 1
        return success

if __name__ == "__main__":
    print("Simple LLM Agent Integration Test")
    print("=" * 40)
    
    agent = SimpleLLMAgent()
    
    # Run 3 test cycles
    for i in range(3):
        try:
            success = agent.run_one_cycle()
            if not success:
                print(f"Cycle {i+1} failed")
                break
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nTest interrupted")
            break
        except Exception as e:
            print(f"Error in cycle {i+1}: {e}")
            break
    
    print(f"\nCompleted {agent.action_count} agent cycles")
    print("Integration test finished!")
