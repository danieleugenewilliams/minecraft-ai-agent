"""
macOS automation for Minecraft AI Agent
Handles keyboard and mouse input automation
"""

import time
import subprocess
from typing import Tuple, Optional
from abc import ABC, abstractmethod

try:
    import pyautogui
    from pynput import mouse, keyboard
    from pynput.mouse import Button
    from pynput.keyboard import Key
except ImportError:
    # Graceful fallback for when dependencies aren't installed
    pyautogui = None
    mouse = None
    keyboard = None
    Button = None
    Key = None


class InputController(ABC):
    """Abstract base class for input controllers"""
    
    @abstractmethod
    def move_mouse(self, x: int, y: int) -> None:
        """Move mouse to coordinates"""
        pass
    
    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at coordinates"""
        pass
    
    @abstractmethod
    def key_press(self, key: str) -> None:
        """Press a key"""
        pass
    
    @abstractmethod
    def key_release(self, key: str) -> None:
        """Release a key"""
        pass
    
    @abstractmethod
    def center_view(self) -> None:
        """Center the camera view"""
        pass


class MacOSInputController(InputController):
    """macOS-specific input controller using pyautogui and pynput"""
    
    def __init__(self, safety_bounds: bool = True, click_duration: float = 0.1):
        if pyautogui is None:
            raise ImportError("pyautogui is required for automation")
        
        self.safety_bounds = safety_bounds
        self.click_duration = click_duration
        
        # Configure pyautogui
        pyautogui.FAILSAFE = safety_bounds
        pyautogui.PAUSE = 0.01  # Small pause between actions
        
        self._mouse_controller = mouse.Controller() if mouse else None
        self._keyboard_controller = keyboard.Controller() if keyboard else None
    
    def focus_minecraft_window(self) -> bool:
        """Try to focus Minecraft window using AppleScript"""
        try:
            # Try iPhone Mirroring app first (where Minecraft is likely running)
            minecraft_names = ["iPhone Mirroring", "Minecraft", "minecraft", "MinecraftLauncher"]
            
            for name in minecraft_names:
                script = f'''
                tell application "System Events"
                    try
                        set targetApp to first application process whose name is "{name}"
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
                    print(f"Successfully focused: {name}")
                    time.sleep(0.5)  # Give time for focus to take effect
                    return True
            
            # Fallback: try to click on iPhone Mirroring window if it exists
            script = '''
            tell application "iPhone Mirroring" to activate
            '''
            try:
                subprocess.run(['osascript', '-e', script], 
                             capture_output=True, text=True, timeout=3)
                time.sleep(0.5)
                return True
            except:
                pass
            
            return False
        except Exception as e:
            print(f"Error focusing window: {e}")
            return False
    
    def move_mouse(self, x: int, y: int) -> None:
        """Move mouse to coordinates"""
        pyautogui.moveTo(x, y)
    
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at coordinates"""
        pyautogui.click(x, y, button=button, duration=self.click_duration)
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, 
             duration: float = 0.5) -> None:
        """Drag from start to end coordinates"""
        pyautogui.drag(end_x - start_x, end_y - start_y, 
                      duration=duration, button='left')
    
    def key_press(self, key: str) -> None:
        """Press a key"""
        pyautogui.keyDown(key)
    
    def key_release(self, key: str) -> None:
        """Release a key"""
        pyautogui.keyUp(key)
    
    def key_tap(self, key: str, duration: float = 0.05) -> None:
        """Tap a key (press and release)"""
        self.key_press(key)
        time.sleep(duration)
        self.key_release(key)
    
    def type_text(self, text: str) -> None:
        """Type text"""
        pyautogui.typewrite(text)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        return pyautogui.position()
    
    def scroll(self, clicks: int) -> None:
        """Scroll mouse wheel"""
        pyautogui.scroll(clicks)
    
    def center_view(self) -> None:
        """Center the camera view (look straight ahead)"""
        self.key_tap('enter')


class DryRunInputController(InputController):
    """Mock input controller for testing (dry run mode)"""
    
    def __init__(self):
        self.actions = []
    
    def move_mouse(self, x: int, y: int) -> None:
        """Log mouse movement"""
        self.actions.append(f"MOVE_MOUSE({x}, {y})")
        print(f"[DRY RUN] Move mouse to ({x}, {y})")
    
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Log mouse click"""
        self.actions.append(f"CLICK({x}, {y}, {button})")
        print(f"[DRY RUN] Click {button} at ({x}, {y})")
    
    def key_press(self, key: str) -> None:
        """Log key press"""
        self.actions.append(f"KEY_PRESS({key})")
        print(f"[DRY RUN] Press key: {key}")
    
    def key_release(self, key: str) -> None:
        """Log key release"""
        self.actions.append(f"KEY_RELEASE({key})")
        print(f"[DRY RUN] Release key: {key}")
    
    def get_actions(self) -> list:
        """Get list of recorded actions"""
        return self.actions.copy()
    
    def clear_actions(self) -> None:
        """Clear recorded actions"""
        self.actions.clear()
    
    def center_view(self) -> None:
        """Log center view action"""
        self.actions.append("CENTER_VIEW()")
        print("[DRY RUN] Center camera view")


def create_input_controller(dry_run: bool = False, **kwargs) -> InputController:
    """Factory function to create appropriate input controller"""
    if dry_run:
        return DryRunInputController()
    else:
        return MacOSInputController(**kwargs)