#!/usr/bin/env python3
"""
Simplified Minecraft AI Chat Interface
Uses existing working components directly without complex imports.
"""
import sys
import time
import subprocess
import pyautogui
import mss
import numpy as np
from PIL import Image
import argparse


def focus_minecraft_window():
    """Focus the iPhone Mirroring app where Minecraft is running"""
    try:
        script = '''tell application "iPhone Mirroring" to activate'''
        subprocess.run(['osascript', '-e', script], 
                     capture_output=True, text=True, timeout=3)
        time.sleep(0.2)
        return True
    except:
        return False


def capture_and_analyze_for_water():
    """Capture screen and analyze for water (from working code)"""
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Water detection - blue color ranges (RGB)
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Water color ranges
        water_colors = [
            [(30, 100, 150), (100, 180, 255)],     # Light blue water
            [(20, 60, 120), (80, 120, 200)],       # Deeper blue water
            [(60, 140, 180), (120, 200, 255)],     # Bright water surface
        ]
        
        total_water_coverage = 0
        for lower, upper in water_colors:
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            total_water_coverage += np.sum(mask) / total_pixels
        
        # Region analysis (6 regions)
        height, width = img_array.shape[:2]
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3],
            'right': img_array[:, 2*width//3:],
            'top': img_array[:height//3, :],
            'middle': img_array[height//3:2*height//3, :],
            'bottom': img_array[2*height//3:, :],
        }
        
        region_water = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            region_coverage = 0
            for lower, upper in water_colors:
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                region_coverage += np.sum(mask) / region_pixels
            region_water[region_name] = region_coverage
        
        return {
            'total_water_coverage': total_water_coverage,
            'region_water': region_water
        }
        
    except Exception as e:
        print(f"Vision error: {e}")
        return None


def capture_and_analyze_for_trees():
    """Capture screen and analyze for trees"""
    try:
        # Capture screen
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Tree detection - green/brown color ranges (RGB)
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Tree color ranges
        tree_colors = [
            [(20, 80, 20), (100, 180, 100)],       # Green leaves
            [(40, 120, 40), (120, 200, 120)],      # Bright green foliage
            [(60, 100, 30), (120, 160, 80)],       # Yellowish green
            [(80, 60, 30), (140, 120, 80)],        # Brown tree trunks
        ]
        
        total_tree_coverage = 0
        for lower, upper in tree_colors:
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            total_tree_coverage += np.sum(mask) / total_pixels
        
        # Region analysis (simplified)
        height, width = img_array.shape[:2]
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3],
            'right': img_array[:, 2*width//3:],
        }
        
        region_tree = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            region_coverage = 0
            for lower, upper in tree_colors:
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                region_coverage += np.sum(mask) / region_pixels
            region_tree[region_name] = region_coverage
        
        return {
            'total_tree_coverage': total_tree_coverage,
            'region_tree': region_tree
        }
        
    except Exception as e:
        print(f"Vision error: {e}")
        return None


def execute_minecraft_command(command, duration=0.5):
    """Execute command in Minecraft"""
    focus_minecraft_window()
    pyautogui.keyDown(command)
    time.sleep(duration)
    pyautogui.keyUp(command)


def get_smart_action(target_type, vision_data, step_count):
    """Get next action based on target and vision data"""
    if not vision_data:
        return 'w'  # Default move forward
    
    if target_type == "water":
        coverage = vision_data['total_water_coverage']
        regions = vision_data['region_water']
        
        # Determine phase
        if coverage < 0.005:
            phase = "SEARCH"
        elif coverage > 0.08:
            phase = "APPROACH"
        else:
            phase = "NAVIGATE"
        
        # Get action based on phase
        if phase == "SEARCH":
            cycle = step_count % 24
            if cycle < 3: return 'j'      # Look left
            elif cycle < 6: return 'l'    # Look right
            elif cycle < 8: return 'i' if cycle == 6 else 'k'  # Look up/down
            elif cycle < 15: return 'w'   # Move forward
            elif cycle < 18: return 'a'   # Turn left
            else: return 'd'              # Turn right
        
        elif phase == "NAVIGATE":
            max_region = max(regions.get('left', 0), regions.get('center', 0), regions.get('right', 0))
            if regions.get('left', 0) == max_region and regions.get('left', 0) > 0.01:
                return 'a' if step_count % 8 < 2 else 'w'
            elif regions.get('right', 0) == max_region and regions.get('right', 0) > 0.01:
                return 'd' if step_count % 8 < 2 else 'w'
            else:
                return 'w'
        
        else:  # APPROACH
            return 'w'
    
    elif target_type == "tree":
        coverage = vision_data['total_tree_coverage'] 
        regions = vision_data['region_tree']
        
        if coverage < 0.01:
            # No trees visible, search
            cycle = step_count % 12
            if cycle < 2: return 'j'      # Look left
            elif cycle < 4: return 'l'    # Look right  
            elif cycle < 8: return 'w'    # Move forward
            else: return 'a' if cycle < 10 else 'd'  # Turn
        else:
            # Trees visible, move toward them
            max_region = max(regions.get('left', 0), regions.get('center', 0), regions.get('right', 0))
            if regions.get('left', 0) == max_region:
                return 'a'
            elif regions.get('right', 0) == max_region:
                return 'd'
            else:
                return 'w'
    
    else:  # exploration or other
        cycle = step_count % 16
        if cycle < 2: return 'j'          # Look left
        elif cycle < 4: return 'l'        # Look right
        elif cycle < 10: return 'w'       # Move forward
        elif cycle < 12: return 'a'       # Turn left
        else: return 'd'                  # Turn right


def execute_find_mission(target_type, max_steps=100):
    """Execute a find mission"""
    print(f"🎯 Starting mission: Find {target_type}")
    print(f"   Max steps: {max_steps}")
    print()
    
    max_coverage = 0.0
    found_target = False
    
    for step in range(max_steps):
        # Analyze current view
        if target_type == "water":
            vision_data = capture_and_analyze_for_water()
            coverage = vision_data['total_water_coverage'] if vision_data else 0
        elif target_type == "tree":
            vision_data = capture_and_analyze_for_trees()
            coverage = vision_data['total_tree_coverage'] if vision_data else 0
        else:
            vision_data = capture_and_analyze_for_water()  # Default
            coverage = vision_data['total_water_coverage'] if vision_data else 0
        
        max_coverage = max(max_coverage, coverage)
        
        # Progress reporting
        if step % 20 == 0 or coverage > 0.05:
            print(f"  Step {step + 1:3d}: {target_type} coverage {coverage:.3%} | Max: {max_coverage:.3%}")
        
        # Check if found
        if coverage > 0.15:  # High confidence
            print(f"\n🏆 SUCCESS! Found {target_type} at step {step + 1}")
            print(f"   Final coverage: {coverage:.3%}")
            found_target = True
            break
        elif coverage > 0.05:  # Medium confidence
            print(f"  🎯 {target_type.title()} detected! Coverage: {coverage:.3%}")
        
        # Get and execute next action
        action = get_smart_action(target_type, vision_data, step)
        execute_minecraft_command(action)
        
        # Small delay
        time.sleep(0.1)
    
    if not found_target:
        if max_coverage > 0.01:
            print(f"\n✅ Located {target_type} (max coverage: {max_coverage:.3%})")
        else:
            print(f"\n❌ Could not find {target_type} after {max_steps} steps")
    
    return found_target or max_coverage > 0.01


def execute_navigate_mission(direction, distance=20):
    """Execute a navigate mission"""
    print(f"🧭 Starting mission: Move {direction}")
    print(f"   Distance: ~{distance} blocks")
    print()
    
    steps_needed = distance // 2  # Rough conversion
    
    for step in range(min(steps_needed, 50)):
        if step % 10 == 0:
            print(f"  Step {step + 1}: Adjusting direction {direction}")
            # Adjust direction
            if direction in ['north', 'south']:
                action = 'i' if step % 20 == 0 else 'k'  # Look up/down
            else:
                action = 'j' if 'west' in direction else 'l'  # Look left/right
        else:
            action = 'w'  # Move forward
        
        execute_minecraft_command(action)
        time.sleep(0.1)
    
    print(f"\n✅ Completed navigation {direction} for {steps_needed} steps")
    return True


def execute_explore_mission(steps=50):
    """Execute an explore mission"""
    print(f"🗺️ Starting mission: Explore area")
    print(f"   Steps: {steps}")
    print()
    
    for step in range(steps):
        # Simple exploration pattern
        cycle = step % 16
        
        if cycle < 2:
            action = 'j'      # Look left
        elif cycle < 4:
            action = 'l'      # Look right
        elif cycle < 10:
            action = 'w'      # Move forward
        elif cycle < 12:
            action = 'a'      # Turn left
        else:
            action = 'd'      # Turn right
        
        execute_minecraft_command(action)
        
        if step % 20 == 0:
            print(f"  Exploration step {step + 1}")
        
        time.sleep(0.1)
    
    print(f"\n✅ Completed exploration for {steps} steps")
    return True


def parse_and_execute_command(command):
    """Parse and execute a natural language command"""
    command = command.lower().strip()
    
    # Find commands
    if any(word in command for word in ['find', 'look for', 'search']):
        if 'water' in command:
            return execute_find_mission('water')
        elif any(tree_word in command for tree_word in ['tree', 'trees', 'wood']):
            return execute_find_mission('tree')
        elif any(animal_word in command for animal_word in ['animal', 'animals', 'cow', 'pig', 'sheep']):
            return execute_find_mission('animal')
        else:
            print("❌ Don't know how to find that. Try 'find water' or 'find trees'")
            return False
    
    # Navigate commands
    elif any(word in command for word in ['go', 'move', 'navigate', 'head']):
        if 'water' in command:
            return execute_find_mission('water')  # Navigate to water = find water
        elif any(direction in command for direction in ['north', 'south', 'east', 'west']):
            direction = next(dir for dir in ['north', 'south', 'east', 'west'] if dir in command)
            # Extract distance if present
            import re
            distance_match = re.search(r'(\d+)', command)
            distance = int(distance_match.group(1)) if distance_match else 20
            return execute_navigate_mission(direction, distance)
        else:
            print("❌ Specify a direction like 'go north' or target like 'go to water'")
            return False
    
    # Explore commands
    elif 'explore' in command:
        # Extract steps if present
        import re
        steps_match = re.search(r'(\d+)', command)
        steps = int(steps_match.group(1)) if steps_match else 50
        return execute_explore_mission(steps)
    
    else:
        print("❌ Don't understand that command")
        print("   Try: 'find water', 'go north', 'explore area'")
        return False


class MinecraftChatAgent:
    """Simple chat interface for Minecraft AI agent"""
    
    def __init__(self):
        self.running = True
        self.command_history = []
    
    def start(self):
        """Start the chat interface"""
        print("🤖 Minecraft AI Agent - Simple Chat Interface")
        print("=" * 50)
        print()
        print("Available commands:")
        print("  🔍 find water          - Search for water")
        print("  🔍 find trees          - Search for trees")
        print("  🧭 go north 20         - Move north 20 blocks")
        print("  🗺️ explore area 50     - Explore for 50 steps")
        print("  status                 - Show status")
        print("  history                - Show command history")
        print("  quit                   - Exit")
        print()
        print("💡 Make sure Minecraft is running in iPhone Mirroring!")
        print()
        
        while self.running:
            try:
                # Get user input
                user_input = input("🎮 Command: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'status':
                    self.show_status()
                    continue
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                elif user_input.lower() == 'help':
                    print("\nAvailable commands: find water, find trees, go north, explore area")
                    continue
                
                # Execute the command
                print()
                start_time = time.time()
                success = parse_and_execute_command(user_input)
                execution_time = time.time() - start_time
                
                # Store in history
                self.command_history.append({
                    'command': user_input,
                    'success': success,
                    'time': execution_time
                })
                
                print(f"\n{'✅' if success else '❌'} Command completed in {execution_time:.1f}s")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def show_status(self):
        """Show agent status"""
        print("\n📊 Agent Status:")
        print(f"  Commands executed: {len(self.command_history)}")
        successful = sum(1 for cmd in self.command_history if cmd['success'])
        print(f"  Successful: {successful}/{len(self.command_history)}")
        if self.command_history:
            print(f"  Last command: {self.command_history[-1]['command']}")
    
    def show_history(self):
        """Show command history"""
        if not self.command_history:
            print("\n📝 No command history yet")
            return
        
        print(f"\n📝 Command History ({len(self.command_history)} items):")
        for i, cmd in enumerate(self.command_history[-10:], 1):  # Show last 10
            status = "✅" if cmd['success'] else "❌"
            print(f"  {i:2d}. {status} {cmd['command']} ({cmd['time']:.1f}s)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Simple Minecraft AI Chat Interface")
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Confirm Minecraft is running in iPhone Mirroring')
    args = parser.parse_args()
    
    if args.ready != 'y':
        print("❌ Please start Minecraft in iPhone Mirroring first, then use --ready y")
        print("\nSteps:")
        print("1. Open iPhone Mirroring app")
        print("2. Launch Minecraft on your iPhone")
        print("3. Enter a world")
        print("4. Run: python minecraft_simple_chat.py --ready y")
        return
    
    try:
        agent = MinecraftChatAgent()
        agent.start()
    except Exception as e:
        print(f"❌ Failed to start chat agent: {e}")


if __name__ == "__main__":
    main()