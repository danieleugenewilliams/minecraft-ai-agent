"""
Pydantic models for defining AI agent goals and actions.
"""
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    URGENT = "urgent"


class TargetType(str, Enum):
    WATER = "water"
    TREE = "tree"
    ANIMAL = "animal"
    STRUCTURE = "structure"
    PLAYER = "player"
    ITEM = "item"


class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"
    SOUTHWEST = "southwest"


class GoalStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseGoal(BaseModel):
    """Base class for all agent goals."""
    priority: Priority = Priority.MEDIUM
    timeout_seconds: Optional[int] = Field(default=300, description="Max time to spend on this goal")
    status: GoalStatus = GoalStatus.PENDING
    description: str = Field(description="Human-readable description of the goal")


class FindGoal(BaseGoal):
    """Goal to find a specific target in the environment."""
    goal_type: Literal["find"] = "find"
    target: TargetType = Field(description="What to look for")
    max_distance: Optional[int] = Field(default=None, description="Maximum blocks to search")
    preferred_direction: Optional[Direction] = Field(default=None, description="Preferred search direction")
    description: str = Field(default="Find target in environment")
    
    def model_post_init(self, __context):
        if self.description == "Find target in environment":
            self.description = f"Find {self.target.value}"


class NavigateGoal(BaseGoal):
    """Goal to navigate to a specific location or target."""
    goal_type: Literal["navigate"] = "navigate"
    target: Optional[TargetType] = Field(default=None, description="Target to navigate to")
    direction: Optional[Direction] = Field(default=None, description="Direction to move")
    distance: Optional[int] = Field(default=None, description="Distance to travel in blocks")
    coordinates: Optional[Dict[str, float]] = Field(default=None, description="Specific coordinates to reach")
    description: str = Field(default="Navigate to target")
    
    def model_post_init(self, __context):
        if self.description == "Navigate to target":
            if self.target:
                self.description = f"Navigate to {self.target.value}"
            elif self.direction:
                dist_str = f" {self.distance} blocks" if self.distance else ""
                self.description = f"Move {self.direction.value}{dist_str}"
            elif self.coordinates:
                self.description = f"Go to coordinates {self.coordinates}"


class ExploreGoal(BaseGoal):
    """Goal to explore an area systematically."""
    goal_type: Literal["explore"] = "explore"
    area_radius: int = Field(default=50, description="Radius in blocks to explore")
    exploration_pattern: Literal["spiral", "grid", "random"] = Field(default="spiral", description="Pattern to use for exploration")
    target_interest: Optional[List[TargetType]] = Field(default=None, description="Things to look for while exploring")
    description: str = Field(default="Explore area")
    
    def model_post_init(self, __context):
        if self.description == "Explore area":
            self.description = f"Explore {self.area_radius} block radius using {self.exploration_pattern} pattern"


class GoalResult(BaseModel):
    """Result of executing a goal."""
    goal_id: str
    status: GoalStatus
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional result data")
    execution_time_seconds: Optional[float] = None
    steps_taken: Optional[int] = None
    distance_traveled: Optional[float] = None


class AgentAction(BaseModel):
    """Represents a specific action the agent can take."""
    action_type: Literal["move", "look", "wait", "scan"]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: Optional[float] = Field(default=None, description="How long to perform this action")


class AgentState(BaseModel):
    """Current state of the agent."""
    current_goal: Optional[BaseGoal] = None
    position: Optional[Dict[str, float]] = None
    facing_direction: Optional[Direction] = None
    health: Optional[float] = None
    inventory: Optional[List[str]] = Field(default_factory=list)
    last_action: Optional[AgentAction] = None
    mission_progress: Optional[Dict[str, Any]] = Field(default_factory=dict)