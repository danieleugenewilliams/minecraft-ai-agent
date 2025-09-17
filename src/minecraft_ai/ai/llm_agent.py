"""
LLM-powered Minecraft AI agent using Ollama
"""

import json
import logging
import time
import requests
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from minecraft_ai.ai.agent import BaseAgent, Action
from minecraft_ai.automation.input_controller import MacOSInputController
from minecraft_ai.vision.screen_capture import MinecraftVision


class OllamaClient:
    """Client for communicating with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(__name__)
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> str:
        """Generate response from Ollama model"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return ""


class LLMMinecraftAgent(BaseAgent):
    """LLM-powered Minecraft agent that uses natural language reasoning"""
    
    def __init__(self, input_controller: MacOSInputController, vision: MinecraftVision, 
                 model: str = "qwen2.5:7b"):
        self.input_controller = input_controller
        self.vision = vision
        self.llm = OllamaClient(model=model)
        self.logger = logging.getLogger(__name__)
        
        # Agent state
        self.last_observation = None
        self.action_history: List[Action] = []
        self.objective = "Build a small shelter by gathering wood and dirt, then constructing a basic structure"
        self.memory = []  # Store important events and learnings
        
        # Control mappings for the LLM to understand
        self.control_guide = {
            "movement": {
                "up": "Move forward (THIS IS THE ONLY MOVEMENT KEY THAT WORKS)",
                "down": "Move backward (doesn't work reliably)",
                "left": "Turn/strafe left (doesn't work for movement)",
                "right": "Turn/strafe right (doesn't work for movement)"
            },
            "camera": {
                "j": "Look left",
                "l": "Look right", 
                "k": "Look down",
                "i": "Look up",
                "enter": "Center camera view (look straight ahead)"
            },
            "actions": {
                "left_click": "Mine/break blocks, attack",
                "right_click": "Place blocks, use items",
                "space": "Jump",
                "shift": "Crouch/sneak"
            },
            "important_notes": [
                "ONLY the UP arrow key works for forward movement",
                "j/k/l/i keys control camera looking, NOT movement",
                "Player often gets stuck spinning - use 'enter' to center view",
                "To explore: alternate between 'up' movement and camera looking"
            ]
        }
    
    def observe(self) -> Dict[str, Any]:
        """Observe current Minecraft environment and add context"""
        try:
            # Get visual analysis
            env_analysis = self.vision.analyze_environment()
            
            # Add agent context
            env_analysis['objective'] = self.objective
            env_analysis['recent_actions'] = [str(a) for a in self.action_history[-5:]]
            env_analysis['control_guide'] = self.control_guide
            
            self.last_observation = env_analysis
            return env_analysis
            
        except Exception as e:
            self.logger.error(f"Error during observation: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    def decide(self, observation: Dict[str, Any]) -> Optional[Action]:
        """Use LLM to decide next action based on observation"""
        if 'error' in observation:
            return None
        
        # Create detailed prompt for the LLM
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(observation)
        
        # Get LLM response
        llm_response = self.llm.generate(user_prompt, system_prompt, temperature=0.2)
        
        if not llm_response:
            self.logger.warning("No response from LLM, using fallback")
            return Action('look_around')  # Safe fallback
        
        # Parse LLM response into action
        action = self._parse_llm_response(llm_response)
        
        if action:
            self.logger.info(f"LLM Decision: {llm_response[:100]}...")
            self.logger.info(f"Action: {action}")
        
        return action
    
    def act(self, action: Action) -> bool:
        """Execute action using input controller with focus handling"""
        try:
            # Focus Minecraft window - check if method exists
            if hasattr(self.input_controller, 'focus_minecraft_window'):
                self.input_controller.focus_minecraft_window()
            
            success = self._execute_action(action)
            
            # Record action
            self.action_history.append(action)
            if len(self.action_history) > 50:
                self.action_history = self.action_history[-50:]
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return False
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the LLM"""
        return f"""You are an AI agent controlling a character in Minecraft through iPhone mirroring. 

OBJECTIVE: {self.objective}

CRITICAL CONTROL INFORMATION:
- ONLY the UP arrow key moves the character forward (this is the ONLY movement that works!)
- j/k/l/i keys control camera looking (NOT movement)
- If character is spinning/stuck, use 'center_view' to reset camera
- To explore: alternate between 'move_forward' (up key) and looking around

AVAILABLE ACTIONS:
- move_forward: Use UP arrow (ONLY working movement)
- look_left: Use j key to turn camera left
- look_right: Use l key to turn camera right  
- look_up: Use i key to look up
- look_down: Use k key to look down
- center_view: Use enter key to center camera
- mine: Left click to break blocks
- place: Right click to place blocks
- jump: Space bar
- wait: Do nothing for one cycle

RESPONSE FORMAT:
Analyze the situation briefly, then respond with exactly one action in this format:
ACTION: [action_name]
REASON: [brief explanation]

Be decisive and specific. Focus on the objective of building a shelter."""
    
    def _create_user_prompt(self, observation: Dict[str, Any]) -> str:
        """Create user prompt with current game state"""
        color_coverage = observation.get('color_coverage', {})
        recent_actions = observation.get('recent_actions', [])
        
        prompt = f"""CURRENT GAME STATE:
Colors visible on screen:
- Wood: {color_coverage.get('wood', 0):.1%}
- Leaves: {color_coverage.get('leaves', 0):.1%}  
- Dirt: {color_coverage.get('dirt', 0):.1%}
- Stone: {color_coverage.get('stone', 0):.1%}
- Grass: {color_coverage.get('grass', 0):.1%}
- Sky: {color_coverage.get('sky', 0):.1%}

Recent actions: {recent_actions[-3:] if recent_actions else 'None'}

What should you do next to work toward building a shelter? Remember:
- Find trees (wood/leaves) to chop for building materials
- Look for dirt to gather for foundation
- Use ONLY 'move_forward' for movement (up arrow key)
- Use looking actions (j/k/l/i) to scan for resources
- If spinning/stuck, use 'center_view' to reset

Choose your next action:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Optional[Action]:
        """Parse LLM response into an Action"""
        try:
            # Look for ACTION: pattern
            lines = response.split('\n')
            action_line = None
            reason_line = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('ACTION:'):
                    action_line = line.replace('ACTION:', '').strip()
                elif line.startswith('REASON:'):
                    reason_line = line.replace('REASON:', '').strip()
            
            if not action_line:
                # Fallback: look for common action words
                response_lower = response.lower()
                if 'move' in response_lower and 'forward' in response_lower:
                    action_line = 'move_forward'
                elif 'look' in response_lower and 'left' in response_lower:
                    action_line = 'look_left'
                elif 'look' in response_lower and 'right' in response_lower:
                    action_line = 'look_right'
                elif 'mine' in response_lower or 'chop' in response_lower:
                    action_line = 'mine'
                elif 'center' in response_lower:
                    action_line = 'center_view'
                else:
                    action_line = 'look_around'
            
            # Create action with reason
            action = Action(action_line, reason=reason_line or "LLM decision")
            return action
            
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return Action('look_around')  # Safe fallback
    
    def _execute_action(self, action: Action) -> bool:
        """Execute the parsed action"""
        action_type = action.action_type
        
        if action_type == 'move_forward':
            self.input_controller.key_press('up')
            time.sleep(0.5)  # Move for half a second
            self.input_controller.key_release('up')
            
        elif action_type == 'look_left':
            self.input_controller.key_press('j')
            time.sleep(0.3)
            self.input_controller.key_release('j')
            
        elif action_type == 'look_right':
            self.input_controller.key_press('l')
            time.sleep(0.3)
            self.input_controller.key_release('l')
            
        elif action_type == 'look_up':
            self.input_controller.key_press('i')
            time.sleep(0.3)
            self.input_controller.key_release('i')
            
        elif action_type == 'look_down':
            self.input_controller.key_press('k')
            time.sleep(0.3)
            self.input_controller.key_release('k')
            
        elif action_type == 'center_view':
            if hasattr(self.input_controller, 'center_view'):
                self.input_controller.center_view()
            else:
                self.input_controller.key_press('enter')
                time.sleep(0.1)
                self.input_controller.key_release('enter')
                
        elif action_type == 'mine':
            # Click to mine
            if hasattr(self.input_controller, 'get_mouse_position'):
                pos = self.input_controller.get_mouse_position()
                self.input_controller.click(pos[0], pos[1], 'left')
            else:
                # Fallback: press and hold left click
                self.input_controller.key_press('button1')
                time.sleep(0.3)
                self.input_controller.key_release('button1')
                
        elif action_type == 'place':
            # Right click to place
            if hasattr(self.input_controller, 'get_mouse_position'):
                pos = self.input_controller.get_mouse_position()
                self.input_controller.click(pos[0], pos[1], 'right')
                
        elif action_type == 'jump':
            self.input_controller.key_press('space')
            time.sleep(0.1)
            self.input_controller.key_release('space')
            
        elif action_type == 'wait':
            time.sleep(0.5)
            
        else:
            # Default: look around
            self.input_controller.key_press('l')
            time.sleep(0.2)
            self.input_controller.key_release('l')
        
        return True