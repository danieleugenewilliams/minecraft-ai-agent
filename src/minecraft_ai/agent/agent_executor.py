"""
Agent executor that processes goals and coordinates vision, control, and navigation.
"""
import time
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Imports with error handling since type checker complains
try:
    from ..models.goals import BaseGoal, GoalResult, GoalStatus, AgentState, TargetType
    from ..vision.vision_system import VisionSystem, VisionResult
    from ..control.control_system import MinecraftController, NavigationPlanner, ActionType
    from ..parsing.goal_parser import GoalParser, ParseResult
except ImportError:
    # Fallback for development
    pass


@dataclass
class ExecutionResult:
    """Result of goal execution."""
    success: bool
    message: str
    goal_result: Optional['GoalResult'] = None
    steps_taken: int = 0
    execution_time: float = 0.0


class AgentExecutor:
    """Main agent executor that coordinates all subsystems."""
    
    def __init__(self):
        # Initialize subsystems
        self.vision_system = VisionSystem()
        self.controller = MinecraftController()
        self.navigation_planner = NavigationPlanner()
        self.goal_parser = GoalParser()
        
        # Agent state
        self.agent_state = AgentState()
        self.current_goal: Optional['BaseGoal'] = None
        self.execution_history: List[ExecutionResult] = []
        self.max_steps_per_goal = 200
        
        # Tracking variables
        self.max_coverage_seen = 0.0
        self.steps_taken = 0
        
    def execute_command(self, command: str) -> ExecutionResult:
        """Execute a natural language command."""
        # Parse the command
        parse_result = self.goal_parser.parse(command)
        
        if not parse_result.success:
            return ExecutionResult(
                success=False,
                message=parse_result.error_message or "Failed to parse command"
            )
        
        # Execute the goal
        return self.execute_goal(parse_result.goal)
    
    def execute_goal(self, goal: 'BaseGoal') -> ExecutionResult:
        """Execute a structured goal."""
        if not goal:
            return ExecutionResult(
                success=False,
                message="No goal provided"
            )
        
        # Set current goal
        self.current_goal = goal
        self.agent_state.current_goal = goal
        goal.status = GoalStatus.IN_PROGRESS
        
        # Generate unique goal ID
        goal_id = str(uuid.uuid4())[:8]
        
        start_time = time.time()
        steps_taken = 0
        success = False
        message = ""
        
        print(f"🎯 Starting goal: {goal.description}")
        print(f"   Goal ID: {goal_id}")
        print(f"   Priority: {goal.priority.value}")
        print(f"   Timeout: {goal.timeout_seconds}s")
        print()
        
        try:
            # Route to appropriate execution method
            if hasattr(goal, 'goal_type'):
                goal_type = getattr(goal, 'goal_type')
                if goal_type == 'find':
                    result = self._execute_find_goal(goal, goal_id)
                elif goal_type == 'navigate':
                    result = self._execute_navigate_goal(goal, goal_id)
                elif goal_type == 'explore':
                    result = self._execute_explore_goal(goal, goal_id)
                else:
                    result = ExecutionResult(
                        success=False,
                        message=f"Unknown goal type: {goal_type}"
                    )
            else:
                result = ExecutionResult(
                    success=False,
                    message="Goal missing goal_type attribute"
                )
            
            success = result.success
            message = result.message
            steps_taken = result.steps_taken
            
        except Exception as e:
            success = False
            message = f"Goal execution failed: {e}"
        
        finally:
            # Update goal status
            goal.status = GoalStatus.COMPLETED if success else GoalStatus.FAILED
            execution_time = time.time() - start_time
            
            # Create goal result
            goal_result = GoalResult(
                goal_id=goal_id,
                status=goal.status,
                success=success,
                message=message,
                execution_time_seconds=execution_time,
                steps_taken=steps_taken
            )
            
            # Create execution result
            exec_result = ExecutionResult(
                success=success,
                message=message,
                goal_result=goal_result,
                steps_taken=steps_taken,
                execution_time=execution_time
            )
            
            # Store in history
            self.execution_history.append(exec_result)
            
            # Reset current goal
            self.current_goal = None
            self.agent_state.current_goal = None
            
            print(f"\n🏁 Goal completed: {goal.description}")
            print(f"   Success: {'✅' if success else '❌'}")
            print(f"   Steps: {steps_taken}")
            print(f"   Time: {execution_time:.1f}s")
            print(f"   Message: {message}")
            
            return exec_result
    
    def _execute_find_goal(self, goal: 'FindGoal', goal_id: str) -> ExecutionResult:
        """Execute a find goal."""
        target = goal.target
        max_steps = min(goal.timeout_seconds // 2, self.max_steps_per_goal)  # Assume 2 seconds per step
        
        print(f"🔍 Searching for {target.value}...")
        
        self.max_coverage_seen = 0.0
        steps_taken = 0
        
        for step in range(max_steps):
            # Analyze current view
            if target == TargetType.WATER:
                vision_result = self.vision_system.analyze_for_water()
            elif target == TargetType.TREE:
                vision_result = self.vision_system.analyze_for_trees()
            else:
                vision_result = self.vision_system.analyze_for_water()  # Default
            
            if not vision_result:
                continue
            
            coverage = vision_result.total_coverage
            self.max_coverage_seen = max(self.max_coverage_seen, coverage)
            
            # Progress reporting
            if step % 20 == 0 or coverage > 0.05:
                print(f"  Step {step + 1:3d}: {target.value} coverage {coverage:.3%} | "
                      f"Max: {self.max_coverage_seen:.3%}")
            
            # Check if found
            if coverage > 0.15:  # High confidence threshold
                return ExecutionResult(
                    success=True,
                    message=f"Found {target.value}! Coverage: {coverage:.3%}",
                    steps_taken=step + 1
                )
            elif coverage > 0.05:  # Medium confidence
                print(f"  🎯 {target.value.title()} detected! Coverage: {coverage:.3%}")
            
            # Get next action from navigation planner
            phase = self.navigation_planner.determine_phase(coverage, step, self.max_coverage_seen)
            action = self.navigation_planner.get_next_action(vision_result, target.value, phase)
            
            # Execute action
            if not self._execute_action(action):
                continue
            
            steps_taken = step + 1
            
            # Small delay between actions
            time.sleep(0.1)
        
        # Goal completed but target not found with high confidence
        if self.max_coverage_seen > 0.01:
            return ExecutionResult(
                success=True,
                message=f"Located {target.value} (max coverage: {self.max_coverage_seen:.3%})",
                steps_taken=steps_taken
            )
        else:
            return ExecutionResult(
                success=False,
                message=f"Could not find {target.value} after {steps_taken} steps",
                steps_taken=steps_taken
            )
    
    def _execute_navigate_goal(self, goal: 'NavigateGoal', goal_id: str) -> ExecutionResult:
        """Execute a navigate goal."""
        # This is a simplified implementation
        # In a full implementation, this would use pathfinding and coordinate tracking
        
        if goal.target:
            print(f"🧭 Navigating to {goal.target.value}...")
            # Use find goal logic but with navigation focus
            find_goal = type('FindGoal', (), {
                'target': goal.target,
                'timeout_seconds': goal.timeout_seconds,
                'description': f"Navigate to {goal.target.value}"
            })()
            return self._execute_find_goal(find_goal, goal_id)
        
        elif goal.direction:
            print(f"🧭 Moving {goal.direction.value}...")
            distance = goal.distance or 20  # Default distance
            steps_needed = distance // 2  # Rough conversion
            
            for step in range(min(steps_needed, 50)):
                # Mostly move forward with some turning
                if step % 10 == 0:
                    # Adjust direction
                    if goal.direction.value in ['north', 'south']:
                        action = ActionType.LOOK_UP if step % 20 == 0 else ActionType.LOOK_DOWN
                    else:
                        action = ActionType.LOOK_LEFT if 'west' in goal.direction.value else ActionType.LOOK_RIGHT
                else:
                    action = ActionType.MOVE_FORWARD
                
                self._execute_action(action)
                time.sleep(0.1)
            
            return ExecutionResult(
                success=True,
                message=f"Moved {goal.direction.value} for {steps_needed} steps",
                steps_taken=steps_needed
            )
        
        else:
            return ExecutionResult(
                success=False,
                message="Navigate goal missing target or direction"
            )
    
    def _execute_explore_goal(self, goal: 'ExploreGoal', goal_id: str) -> ExecutionResult:
        """Execute an explore goal."""
        print(f"🗺️ Exploring area (radius: {goal.area_radius}, pattern: {goal.exploration_pattern})...")
        
        steps_taken = 0
        max_steps = min(goal.timeout_seconds // 2, 100)
        
        for step in range(max_steps):
            # Simple exploration pattern
            cycle = step % 16
            
            if cycle < 2:
                action = ActionType.LOOK_LEFT
            elif cycle < 4:
                action = ActionType.LOOK_RIGHT
            elif cycle < 10:
                action = ActionType.MOVE_FORWARD
            elif cycle < 12:
                action = ActionType.MOVE_LEFT
            else:
                action = ActionType.MOVE_RIGHT
            
            self._execute_action(action)
            steps_taken += 1
            
            # Progress reporting
            if step % 20 == 0:
                print(f"  Exploration step {step + 1}")
            
            time.sleep(0.1)
        
        return ExecutionResult(
            success=True,
            message=f"Explored area for {steps_taken} steps",
            steps_taken=steps_taken
        )
    
    def _execute_action(self, action: ActionType) -> bool:
        """Execute a single action."""
        try:
            if action == ActionType.MOVE_FORWARD:
                return self.controller.move_forward()
            elif action == ActionType.MOVE_BACKWARD:
                return self.controller.move_backward()
            elif action == ActionType.MOVE_LEFT:
                return self.controller.turn_left()
            elif action == ActionType.MOVE_RIGHT:
                return self.controller.turn_right()
            elif action == ActionType.LOOK_LEFT:
                return self.controller.look_left()
            elif action == ActionType.LOOK_RIGHT:
                return self.controller.look_right()
            elif action == ActionType.LOOK_UP:
                return self.controller.look_up()
            elif action == ActionType.LOOK_DOWN:
                return self.controller.look_down()
            elif action == ActionType.WAIT:
                return self.controller.wait()
            else:
                return False
        except Exception as e:
            print(f"Action execution failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'current_goal': self.current_goal.description if self.current_goal else None,
            'goal_status': self.current_goal.status.value if self.current_goal else None,
            'steps_taken': self.steps_taken,
            'max_coverage_seen': self.max_coverage_seen,
            'execution_history_count': len(self.execution_history),
            'last_execution': self.execution_history[-1].message if self.execution_history else None
        }