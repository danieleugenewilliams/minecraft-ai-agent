"""
Basic AI agent framework for Minecraft
"""

import time
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from minecraft_ai.core.config import Config
from minecraft_ai.automation.input_controller import create_input_controller, InputController
from minecraft_ai.vision.screen_capture import create_screen_capture, MinecraftVision


class Action:
    """Represents an action the agent can take"""
    
    def __init__(self, action_type: str, **kwargs):
        self.action_type = action_type
        self.params = kwargs
        self.timestamp = time.time()
    
    def __str__(self):
        return f"Action({self.action_type}, {self.params})"


class BaseAgent(ABC):
    """Abstract base class for AI agents"""
    
    @abstractmethod
    def observe(self) -> Dict[str, Any]:
        """Observe the current environment"""
        pass
    
    @abstractmethod
    def decide(self, observation: Dict[str, Any]) -> Optional[Action]:
        """Decide what action to take based on observation"""
        pass
    
    @abstractmethod
    def act(self, action: Action) -> bool:
        """Execute the decided action"""
        pass


class RuleBasedAgent(BaseAgent):
    """Simple rule-based agent for basic Minecraft tasks with shelter building"""
    
    def __init__(self, input_controller: InputController, vision: MinecraftVision):
        self.input_controller = input_controller
        self.vision = vision
        self.logger = logging.getLogger(__name__)
        
        # State tracking for shelter building
        self.last_observation = None
        self.action_history: List[Action] = []
        self.stuck_counter = 0
        
        # Resource tracking (estimated)
        self.estimated_resources = {
            'wood': 0,
            'dirt': 0,
            'stone': 0
        }
        
        # Building phase tracking
        self.building_phase = 'exploring'  # exploring -> gathering -> building -> shelter_complete
        self.gathering_target = None  # Current resource we're looking for
        self.wood_gathered = 0
        self.dirt_gathered = 0
        self.target_wood = 15  # Enough for basic shelter
        self.target_dirt = 20  # For foundation/walls
        self.mining_attempts = 0  # Track how long we've been mining same spot
        self.last_wood_count = 0  # Track if we're making progress
        
    def observe(self) -> Dict[str, Any]:
        """Observe current Minecraft environment"""
        try:
            # Get visual analysis
            env_analysis = self.vision.analyze_environment()
            
            # Add mouse position for context
            if hasattr(self.input_controller, 'get_mouse_position'):
                mouse_pos = self.input_controller.get_mouse_position()
                env_analysis['mouse_position'] = mouse_pos
            
            self.last_observation = env_analysis
            return env_analysis
            
        except Exception as e:
            self.logger.error(f"Error during observation: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    def decide(self, observation: Dict[str, Any]) -> Optional[Action]:
        """Shelter-focused decision making with resource gathering priority"""
        if 'error' in observation:
            return None
        
        color_coverage = observation.get('color_coverage', {})
        
        # Update building phase based on resources
        if self.building_phase == 'exploring':
            if self.wood_gathered < self.target_wood:
                self.gathering_target = 'wood'
                self.building_phase = 'gathering_wood'
            elif self.dirt_gathered < self.target_dirt:
                self.gathering_target = 'dirt'
                self.building_phase = 'gathering_dirt'
            else:
                self.building_phase = 'building'
        
        # PHASE 1: GATHERING WOOD - Highest priority for trees
        if self.building_phase == 'gathering_wood':
            wood_coverage = color_coverage.get('wood', 0)
            leaves_coverage = color_coverage.get('leaves', 0)
            
            # Check if we're making progress
            if self.wood_gathered == self.last_wood_count:
                self.mining_attempts += 1
            else:
                self.mining_attempts = 0
                self.last_wood_count = self.wood_gathered
            
            # If we've been mining the same spot too long, move to explore
            if self.mining_attempts > 8:  # 8 attempts = ~0.8 seconds
                self.mining_attempts = 0
                import random
                if random.random() < 0.7:
                    return Action('move_forward')  # Move to find new trees
                else:
                    return Action('look_around')   # Look for trees
            
            # Strong focus on finding and chopping trees
            if wood_coverage > 0.02 or leaves_coverage > 0.08:
                self.wood_gathered += 0.5  # Estimate wood collected
                return Action('mine', target='wood', priority='high')
            
            # If no trees visible, actively explore to find them
            elif color_coverage.get('grass', 0) > 0.1:
                # Move in patterns to find trees
                import random
                if random.random() < 0.6:
                    return Action('move_forward')
                else:
                    return Action('look_around')
            else:
                return Action('explore_for_trees')
        
        # PHASE 2: GATHERING DIRT - Focus on dirt after wood
        elif self.building_phase == 'gathering_dirt':
            dirt_coverage = color_coverage.get('dirt', 0)
            
            # Mine dirt when found
            if dirt_coverage > 0.03:
                self.dirt_gathered += 0.3  # Estimate dirt collected
                return Action('mine', target='dirt', priority='high')
            
            # Look for dirt patches
            elif color_coverage.get('grass', 0) > 0.15:
                # Dig down to find dirt under grass
                return Action('mine', target='dirt_under_grass')
            
            # Explore to find dirt areas
            else:
                return Action('explore_for_dirt')
        
        # PHASE 3: BUILDING SHELTER
        elif self.building_phase == 'building':
            return Action('build_shelter')
        
        # FALLBACK: General exploration with resource focus
        else:
            # Still prioritize visible resources even while exploring
            wood_coverage = color_coverage.get('wood', 0)
            leaves_coverage = color_coverage.get('leaves', 0)
            dirt_coverage = color_coverage.get('dirt', 0)
            
            # Always mine trees if visible - most valuable resource
            if wood_coverage > 0.02 or leaves_coverage > 0.08:
                return Action('mine', target='wood', priority='critical')
            
            # Mine dirt if abundant
            elif dirt_coverage > 0.05:
                return Action('mine', target='dirt', priority='high')
            
            # Stone is secondary priority
            elif color_coverage.get('stone', 0) > 0.03:
                return Action('mine', target='stone', priority='medium')
            
            # If mostly sky, look around strategically for resources
            elif color_coverage.get('sky', 0) > 0.3:
                import random
                if random.random() < 0.4:
                    return Action('center_view')  # Reset view to see terrain
                else:
                    return Action('look_around')
            
            # Default exploration with resource-seeking movement
            else:
                import random
                if random.random() < 0.5:
                    return Action('move_forward')
                elif random.random() < 0.2:
                    return Action('center_view')
                else:
                    return Action('look_around')
    
    def act(self, action: Action) -> bool:
        """Execute action using input controller"""
        try:
            # Try to focus Minecraft window before sending input
            if hasattr(self.input_controller, 'focus_minecraft_window'):
                focus_success = self.input_controller.focus_minecraft_window()
                if not focus_success:
                    self.logger.warning("Could not focus Minecraft window - input may not work")
            
            action_type = action.action_type
            
            # Minecraft movement controls - using working key combinations
            if action_type == 'move_forward':
                self.input_controller.key_press('up')  # up smooth (works)
                time.sleep(0.3)
                self.input_controller.key_release('up')
                
            elif action_type == 'move_backward':
                self.input_controller.key_press('k')  # down precise (works)
                time.sleep(0.3)
                self.input_controller.key_release('k')
                
            elif action_type == 'move_left':
                self.input_controller.key_press('j')  # left precise (works)
                time.sleep(0.3)
                self.input_controller.key_release('j')
                
            elif action_type == 'move_right':
                self.input_controller.key_press('l')  # right precise (works)
                time.sleep(0.3)
                self.input_controller.key_release('l')
                
            elif action_type == 'look_up':
                self.input_controller.key_press('i')  # up precise
                time.sleep(0.2)
                self.input_controller.key_release('i')
                
            elif action_type == 'look_down':
                self.input_controller.key_press('k')  # down precise
                time.sleep(0.2)
                self.input_controller.key_release('k')
                
            elif action_type == 'look_left':
                self.input_controller.key_press('j')  # left precise
                time.sleep(0.2)
                self.input_controller.key_release('j')
                
            elif action_type == 'look_right':
                self.input_controller.key_press('l')  # right precise
                time.sleep(0.2)
                self.input_controller.key_release('l')
                
            elif action_type == 'jump':
                self.input_controller.key_tap('space', 0.1)
                
            elif action_type == 'crouch':
                self.input_controller.key_press('shift')
                time.sleep(0.5)
                self.input_controller.key_release('shift')
                
            elif action_type == 'toggle_fly':
                # Double tap space for fly mode
                self.input_controller.key_tap('space', 0.05)
                time.sleep(0.1)
                self.input_controller.key_tap('space', 0.05)
                
            elif action_type == 'turn_right':
                # Mouse look right
                current_pos = getattr(self.input_controller, 'get_mouse_position', lambda: (500, 500))()
                new_x = current_pos[0] + 50
                self.input_controller.move_mouse(new_x, current_pos[1])
                
            elif action_type == 'turn_left':
                # Mouse look left
                current_pos = getattr(self.input_controller, 'get_mouse_position', lambda: (500, 500))()
                new_x = current_pos[0] - 50
                self.input_controller.move_mouse(new_x, current_pos[1])
                
            elif action_type == 'mine':
                # Left click to mine/break blocks
                current_pos = getattr(self.input_controller, 'get_mouse_position', lambda: (500, 500))()
                target = action.params.get('target', 'unknown')
                if target == 'wood':
                    # Hold click longer for chopping wood
                    self.input_controller.click(current_pos[0], current_pos[1], 'left')
                    time.sleep(0.3)  # Longer hold for wood chopping
                else:
                    # Regular mining for stone/blocks
                    self.input_controller.click(current_pos[0], current_pos[1], 'left')
                    time.sleep(0.1)
                
            elif action_type == 'look_around':
                # Random mouse movement to look around
                current_pos = getattr(self.input_controller, 'get_mouse_position', lambda: (500, 500))()
                import random
                new_x = current_pos[0] + random.randint(-30, 30)
                new_y = current_pos[1] + random.randint(-10, 10)
                self.input_controller.move_mouse(new_x, new_y)
                
            elif action_type == 'center_view':
                # Use enter key to center camera view
                if hasattr(self.input_controller, 'center_view'):
                    self.input_controller.center_view()
                else:
                    self.input_controller.key_tap('enter')
                    
            elif action_type == 'explore_for_trees':
                # Systematic exploration to find trees
                import random
                if random.random() < 0.7:
                    # Move forward to cover ground
                    self.input_controller.key_press('up')
                    time.sleep(0.4)
                    self.input_controller.key_release('up')
                else:
                    # Turn to scan for trees
                    self.input_controller.key_press('l')
                    time.sleep(0.3)
                    self.input_controller.key_release('l')
                    
            elif action_type == 'explore_for_dirt':
                # Look for dirt patches or dig down
                import random
                if random.random() < 0.5:
                    # Look down to find dirt
                    self.input_controller.key_press('k')
                    time.sleep(0.2)
                    self.input_controller.key_release('k')
                else:
                    # Move to find dirt areas
                    self.input_controller.key_press('up')
                    time.sleep(0.3)
                    self.input_controller.key_release('up')
                    
            elif action_type == 'build_shelter':
                # Basic shelter building - place blocks
                current_pos = getattr(self.input_controller, 'get_mouse_position', lambda: (500, 500))()
                
                # Right click to place blocks (if we have them)
                self.input_controller.click(current_pos[0], current_pos[1], 'right')
                time.sleep(0.2)
                
                # Move to build in a pattern (simple 3x3 foundation)
                import random
                if random.random() < 0.5:
                    # Move to next building position
                    direction = random.choice(['j', 'l'])  # left or right
                    self.input_controller.key_press(direction)
                    time.sleep(0.2)
                    self.input_controller.key_release(direction)
            
            # Record action and update status
            self.action_history.append(action)
            if len(self.action_history) > 100:  # Keep last 100 actions
                self.action_history = self.action_history[-100:]
            
            # Log current status for user visibility
            self._log_status(action)
            
            self.logger.debug(f"Executed action: {action}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return False
    
    def _log_status(self, action: Action) -> None:
        """Log current building progress for user visibility"""
        status_msg = f"Phase: {self.building_phase} | Wood: {self.wood_gathered:.1f}/{self.target_wood} | Dirt: {self.dirt_gathered:.1f}/{self.target_dirt} | Action: {action.action_type}"
        
        if action.params.get('target'):
            status_msg += f" ({action.params['target']})"
        if action.params.get('priority'):
            status_msg += f" [Priority: {action.params['priority']}]"
            
        self.logger.info(status_msg)


class MinecraftAgent:
    """Main Minecraft AI agent orchestrator"""
    
    def __init__(self, config: Config, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.input_controller = create_input_controller(
            dry_run=dry_run,
            safety_bounds=config.get('automation.safety_bounds', True),
            click_duration=config.get('automation.click_duration', 0.1)
        )
        
        self.screen_capture = create_screen_capture('mss')
        self.vision = MinecraftVision(
            self.screen_capture,
            image_scale=config.get('vision.image_scale', 0.5),
            color_space=config.get('vision.color_space', 'RGB')
        )
        
        # Create agent based on config
        agent_type = config.get('ai.model_type', 'rule_based')
        if agent_type == 'rule_based':
            self.agent = RuleBasedAgent(self.input_controller, self.vision)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        self.running = False
        self.update_rate = config.get('agent.update_rate', 0.1)
    
    def run(self) -> None:
        """Main agent loop"""
        self.logger.info("Starting Minecraft AI agent...")
        self.running = True
        
        try:
            while self.running:
                # Agent cycle: observe -> decide -> act
                observation = self.agent.observe()
                action = self.agent.decide(observation)
                
                if action:
                    success = self.agent.act(action)
                    if not success:
                        self.logger.warning(f"Failed to execute action: {action}")
                
                # Wait before next cycle
                time.sleep(self.update_rate)
                
        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Agent error: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the agent"""
        self.running = False
        self.logger.info("Minecraft AI agent stopped")