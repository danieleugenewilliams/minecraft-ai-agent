#!/usr/bin/env python3
"""
Minecraft AI Agent Chat Interface

A conversational interface for commanding the Minecraft AI agent.
"""
import sys
import time
import argparse
from typing import Optional

# Import our agent system with error handling
try:
    from src.minecraft_ai.agent.agent_executor import AgentExecutor
    from src.minecraft_ai.models.goals import Priority, TargetType, Direction
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class MinecraftChatAgent:
    """Chat interface for the Minecraft AI agent."""
    
    def __init__(self):
        self.agent = AgentExecutor()
        self.running = True
        self.session_start_time = time.time()
        
    def start(self):
        """Start the chat interface."""
        self.print_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = input("\n🎮 Command: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if self.handle_special_commands(user_input):
                    continue
                
                # Execute the command
                print(f"\n💭 Processing: {user_input}")
                result = self.agent.execute_command(user_input)
                
                # Display result
                self.display_result(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
    
    def print_welcome(self):
        """Print welcome message."""
        print("🤖 Minecraft AI Agent Chat Interface")
        print("=" * 50)
        print()
        print("Commands you can try:")
        print("  🔍 find water          - Search for water")
        print("  🔍 find trees          - Search for trees") 
        print("  🧭 go north            - Move in a direction")
        print("  🧭 navigate to water   - Go to water source")
        print("  🗺️ explore area        - Explore around")
        print()
        print("Special commands:")
        print("  status  - Show agent status")
        print("  history - Show execution history")
        print("  help    - Show this help")
        print("  quit    - Exit the chat")
        print()
        print("💡 Make sure Minecraft is running in iPhone Mirroring!")
        print()
    
    def handle_special_commands(self, command: str) -> bool:
        """Handle special non-goal commands. Returns True if handled."""
        command = command.lower()
        
        if command in ['quit', 'exit', 'bye']:
            self.running = False
            return True
        
        elif command in ['help', '?']:
            self.print_welcome()
            return True
        
        elif command == 'status':
            self.show_status()
            return True
        
        elif command == 'history':
            self.show_history()
            return True
        
        elif command == 'clear':
            self.clear_screen()
            return True
        
        return False
    
    def show_status(self):
        """Show current agent status."""
        status = self.agent.get_status()
        
        print("\n📊 Agent Status:")
        print(f"  Current Goal: {status.get('current_goal', 'None')}")
        print(f"  Goal Status: {status.get('goal_status', 'None')}")
        print(f"  Steps Taken: {status.get('steps_taken', 0)}")
        print(f"  Max Coverage: {status.get('max_coverage_seen', 0):.3%}")
        print(f"  Executions: {status.get('execution_history_count', 0)}")
        print(f"  Last Result: {status.get('last_execution', 'None')}")
        
        # Session info
        session_time = time.time() - self.session_start_time
        print(f"  Session Time: {session_time:.1f}s")
    
    def show_history(self):
        """Show execution history."""
        history = self.agent.execution_history
        
        if not history:
            print("\n📝 No execution history yet")
            return
        
        print(f"\n📝 Execution History ({len(history)} items):")
        
        for i, result in enumerate(history[-10:], 1):  # Show last 10
            status_icon = "✅" if result.success else "❌"
            print(f"  {i:2d}. {status_icon} {result.message}")
            print(f"      Steps: {result.steps_taken}, Time: {result.execution_time:.1f}s")
    
    def display_result(self, result):
        """Display execution result."""
        if result.success:
            print(f"\n✅ Success: {result.message}")
        else:
            print(f"\n❌ Failed: {result.message}")
        
        print(f"   Steps taken: {result.steps_taken}")
        print(f"   Time: {result.execution_time:.1f}s")
        
        if result.goal_result and result.goal_result.data:
            print(f"   Additional data: {result.goal_result.data}")
    
    def clear_screen(self):
        """Clear the screen."""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
        self.print_welcome()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Minecraft AI Agent Chat Interface")
    parser.add_argument('--ready', choices=['y', 'n'], default='n',
                       help='Confirm you have Minecraft running in iPhone Mirroring')
    args = parser.parse_args()
    
    if args.ready != 'y':
        print("❌ Please start Minecraft in iPhone Mirroring first, then use --ready y")
        print("\nSteps:")
        print("1. Open iPhone Mirroring app")
        print("2. Launch Minecraft on your iPhone")
        print("3. Enter a world and position yourself")
        print("4. Run: python minecraft_chat.py --ready y")
        return
    
    # Start the chat interface
    try:
        chat_agent = MinecraftChatAgent()
        chat_agent.start()
    except Exception as e:
        print(f"❌ Failed to start chat agent: {e}")
        return


if __name__ == "__main__":
    main()