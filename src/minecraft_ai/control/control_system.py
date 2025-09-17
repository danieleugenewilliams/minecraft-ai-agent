"""
Control system for Minecraft agent actions and navigation.
"""
import time
import subprocess
import pyautogui
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    MOVE_FORWARD = "w"
    MOVE_BACKWARD = "s" 
    MOVE_LEFT = "a"
    MOVE_RIGHT = "d"
    LOOK_LEFT = "j"
    LOOK_RIGHT = "l"
    LOOK_UP = "i"
    LOOK_DOWN = "k"
    WAIT = "wait"


@dataclass
class ControlAction:
    """Represents a control action to execute."""
    action: ActionType
    duration: float = 0.5
    target_app: str = "iPhone Mirroring"


class WindowManager:
    """Manages window focus for sending commands."""
    
    @staticmethod
    def focus_app(app_name: str) -> bool:
        """Focus a specific application using AppleScript."""
        try:
            script = f'tell application "{app_name}" to activate'
            subprocess.run(['osascript', '-e', script], 
                         capture_output=True, text=True, timeout=3)
            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"Failed to focus {app_name}: {e}")
            return False


class MinecraftController:
    """Handles Minecraft game controls via iPhone Mirroring."""
    
    def __init__(self, target_app: str = "iPhone Mirroring"):
        self.target_app = target_app
        self.window_manager = WindowManager()
    
    def execute_action(self, action: ControlAction) -> bool:
        """Execute a single control action."""
        # Focus the target app
        if not self.window_manager.focus_app(action.target_app):
            return False
        
        if action.action == ActionType.WAIT:
            time.sleep(action.duration)
            return True
        
        # Execute the key command
        try:
            pyautogui.keyDown(action.action.value)
            time.sleep(action.duration)
            pyautogui.keyUp(action.action.value)
            return True
        except Exception as e:
            print(f"Failed to execute action {action.action}: {e}")
            return False
    
    def move_forward(self, duration: float = 0.5) -> bool:
        """Move forward."""
        action = ControlAction(ActionType.MOVE_FORWARD, duration, self.target_app)
        return self.execute_action(action)
    
    def move_backward(self, duration: float = 0.5) -> bool:
        """Move backward."""
        action = ControlAction(ActionType.MOVE_BACKWARD, duration, self.target_app)
        return self.execute_action(action)
    
    def turn_left(self, duration: float = 0.5) -> bool:
        """Turn left (strafe)."""
        action = ControlAction(ActionType.MOVE_LEFT, duration, self.target_app)
        return self.execute_action(action)
    
    def turn_right(self, duration: float = 0.5) -> bool:
        """Turn right (strafe)."""
        action = ControlAction(ActionType.MOVE_RIGHT, duration, self.target_app)
        return self.execute_action(action)
    
    def look_left(self, duration: float = 0.3) -> bool:
        """Look left (camera)."""
        action = ControlAction(ActionType.LOOK_LEFT, duration, self.target_app)
        return self.execute_action(action)
    
    def look_right(self, duration: float = 0.3) -> bool:
        """Look right (camera)."""
        action = ControlAction(ActionType.LOOK_RIGHT, duration, self.target_app)
        return self.execute_action(action)
    
    def look_up(self, duration: float = 0.3) -> bool:
        """Look up (camera)."""
        action = ControlAction(ActionType.LOOK_UP, duration, self.target_app)
        return self.execute_action(action)
    
    def look_down(self, duration: float = 0.3) -> bool:
        """Look down (camera)."""
        action = ControlAction(ActionType.LOOK_DOWN, duration, self.target_app)
        return self.execute_action(action)
    
    def wait(self, duration: float = 1.0) -> bool:
        """Wait for specified duration."""
        action = ControlAction(ActionType.WAIT, duration, self.target_app)
        return self.execute_action(action)


class NavigationPlanner:
    """Plans navigation sequences based on vision data and goals."""
    
    def __init__(self):
        self.current_phase = "SEARCH"
        self.step_count = 0
    
    def get_next_action(self, vision_result, target_type: str, current_phase: Optional[str] = None) -> ActionType:
        """Get the next action based on vision analysis."""
        if current_phase:
            self.current_phase = current_phase
        
        self.step_count += 1
        
        if target_type.lower() == "water":
            return self._plan_water_search(vision_result)
        elif target_type.lower() == "tree":
            return self._plan_tree_search(vision_result)
        else:
            return self._plan_exploration()
    
    def _plan_water_search(self, vision_result) -> ActionType:
        """Plan actions for water search."""
        coverage = vision_result.total_coverage
        regions = vision_result.region_coverage
        
        if self.current_phase == "SEARCH":
            # Structured search pattern - avoid excessive spinning
            search_cycle = self.step_count % 24
            if search_cycle < 3:
                return ActionType.LOOK_LEFT
            elif search_cycle < 6:
                return ActionType.LOOK_RIGHT
            elif search_cycle < 8:
                return ActionType.LOOK_UP if search_cycle == 6 else ActionType.LOOK_DOWN
            elif search_cycle < 15:
                return ActionType.MOVE_FORWARD
            elif search_cycle < 18:
                return ActionType.MOVE_LEFT
            else:
                return ActionType.MOVE_RIGHT
        
        elif self.current_phase == "NAVIGATE":
            # Move toward water
            max_region = max(regions.get('left', 0), regions.get('center', 0), regions.get('right', 0))
            
            if regions.get('left', 0) == max_region and regions.get('left', 0) > 0.01:
                if self.step_count % 8 < 2:
                    return ActionType.MOVE_LEFT
                else:
                    return ActionType.MOVE_FORWARD
            elif regions.get('right', 0) == max_region and regions.get('right', 0) > 0.01:
                if self.step_count % 8 < 2:
                    return ActionType.MOVE_RIGHT
                else:
                    return ActionType.MOVE_FORWARD
            else:
                return ActionType.MOVE_FORWARD
        
        else:  # APPROACH phase
            if coverage > 0.08:
                return ActionType.MOVE_FORWARD
            else:
                return ActionType.MOVE_FORWARD
    
    def _plan_tree_search(self, vision_result) -> ActionType:
        """Plan actions for tree search."""
        coverage = vision_result.total_coverage
        regions = vision_result.region_coverage
        
        # Simple tree search logic
        if coverage < 0.01:
            # No trees visible, explore
            cycle = self.step_count % 12
            if cycle < 2:
                return ActionType.LOOK_LEFT
            elif cycle < 4:
                return ActionType.LOOK_RIGHT
            elif cycle < 8:
                return ActionType.MOVE_FORWARD
            else:
                return ActionType.MOVE_LEFT if cycle < 10 else ActionType.MOVE_RIGHT
        else:
            # Trees visible, move toward them
            max_region = max(regions.get('left', 0), regions.get('center', 0), regions.get('right', 0))
            
            if regions.get('left', 0) == max_region:
                return ActionType.MOVE_LEFT
            elif regions.get('right', 0) == max_region:
                return ActionType.MOVE_RIGHT
            else:
                return ActionType.MOVE_FORWARD
    
    def _plan_exploration(self) -> ActionType:
        """Plan general exploration actions."""
        cycle = self.step_count % 16
        if cycle < 2:
            return ActionType.LOOK_LEFT
        elif cycle < 4:
            return ActionType.LOOK_RIGHT
        elif cycle < 10:
            return ActionType.MOVE_FORWARD
        elif cycle < 12:
            return ActionType.MOVE_LEFT
        else:
            return ActionType.MOVE_RIGHT
    
    def determine_phase(self, coverage: float, step_num: int, max_coverage_seen: float) -> str:
        """Determine current mission phase."""
        if coverage < 0.005 and max_coverage_seen < 0.01 and step_num < 80:
            return "SEARCH"
        elif coverage > 0.08 or max_coverage_seen > 0.08:
            return "APPROACH"
        else:
            return "NAVIGATE"