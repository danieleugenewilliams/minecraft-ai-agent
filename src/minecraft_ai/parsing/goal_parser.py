"""
Goal parser for converting natural language to structured Pydantic goals.
"""
import re
from typing import Optional, Union, List
from dataclasses import dataclass

# Importing our models with error handling since type checker complains
try:
    from ..models.goals import (
        FindGoal, NavigateGoal, ExploreGoal, BaseGoal,
        TargetType, Direction, Priority
    )
except ImportError:
    # Fallback for development - these will be available at runtime
    pass


@dataclass
class ParseResult:
    """Result of parsing natural language input."""
    success: bool
    goal: Optional['BaseGoal'] = None
    error_message: Optional[str] = None
    confidence: float = 0.0


class GoalParser:
    """Parses natural language commands into structured goal objects."""
    
    def __init__(self):
        # Pattern definitions for different goal types
        self.find_patterns = [
            r"find\s+(water|tree|animal|structure|player|item)",
            r"look\s+for\s+(water|tree|animal|structure|player|item)",
            r"search\s+for\s+(water|tree|animal|structure|player|item)",
            r"locate\s+(water|tree|animal|structure|player|item)",
        ]
        
        self.navigate_patterns = [
            r"go\s+to\s+(water|tree|animal|structure|player|item)",
            r"navigate\s+to\s+(water|tree|animal|structure|player|item)",
            r"move\s+to\s+(water|tree|animal|structure|player|item)",
            r"walk\s+to\s+(water|tree|animal|structure|player|item)",
            r"go\s+(north|south|east|west|left|right)",
            r"move\s+(north|south|east|west|left|right)",
            r"head\s+(north|south|east|west|left|right)",
        ]
        
        self.explore_patterns = [
            r"explore\s+(?:the\s+)?area",
            r"explore\s+around",
            r"look\s+around",
            r"scout\s+(?:the\s+)?area",
            r"survey\s+(?:the\s+)?area",
        ]
        
        # Priority indicators
        self.priority_keywords = {
            'urgent': Priority.URGENT,
            'high': Priority.HIGH,
            'important': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW,
            'quick': Priority.HIGH,
            'slowly': Priority.LOW,
        }
        
        # Direction mappings
        self.direction_mappings = {
            'north': Direction.NORTH,
            'south': Direction.SOUTH,
            'east': Direction.EAST,
            'west': Direction.WEST,
            'left': Direction.WEST,  # Relative to current facing
            'right': Direction.EAST,  # Relative to current facing
        }
        
        # Target type mappings
        self.target_mappings = {
            'water': TargetType.WATER,
            'tree': TargetType.TREE,
            'trees': TargetType.TREE,
            'animal': TargetType.ANIMAL,
            'animals': TargetType.ANIMAL,
            'structure': TargetType.STRUCTURE,
            'building': TargetType.STRUCTURE,
            'player': TargetType.PLAYER,
            'item': TargetType.ITEM,
        }
    
    def parse(self, text: str) -> ParseResult:
        """Parse natural language text into a goal object."""
        text = text.lower().strip()
        
        # Try to identify goal type and extract parameters
        find_result = self._try_parse_find_goal(text)
        if find_result.success:
            return find_result
        
        navigate_result = self._try_parse_navigate_goal(text)
        if navigate_result.success:
            return navigate_result
        
        explore_result = self._try_parse_explore_goal(text)
        if explore_result.success:
            return explore_result
        
        return ParseResult(
            success=False,
            error_message=f"Could not understand command: '{text}'. Try 'find water', 'go north', or 'explore area'."
        )
    
    def _try_parse_find_goal(self, text: str) -> ParseResult:
        """Try to parse a find goal."""
        for pattern in self.find_patterns:
            match = re.search(pattern, text)
            if match:
                target_text = match.group(1)
                target = self.target_mappings.get(target_text)
                
                if target:
                    priority = self._extract_priority(text)
                    max_distance = self._extract_distance(text)
                    preferred_direction = self._extract_direction(text)
                    
                    try:
                        goal = FindGoal(
                            target=target,
                            priority=priority,
                            max_distance=max_distance,
                            preferred_direction=preferred_direction
                        )
                        return ParseResult(success=True, goal=goal, confidence=0.9)
                    except Exception as e:
                        return ParseResult(success=False, error_message=f"Failed to create find goal: {e}")
        
        return ParseResult(success=False)
    
    def _try_parse_navigate_goal(self, text: str) -> ParseResult:
        """Try to parse a navigate goal."""
        for pattern in self.navigate_patterns:
            match = re.search(pattern, text)
            if match:
                target_or_direction = match.group(1)
                
                # Check if it's a direction
                direction = self.direction_mappings.get(target_or_direction)
                if direction:
                    priority = self._extract_priority(text)
                    distance = self._extract_distance(text)
                    
                    try:
                        goal = NavigateGoal(
                            direction=direction,
                            distance=distance,
                            priority=priority
                        )
                        return ParseResult(success=True, goal=goal, confidence=0.9)
                    except Exception as e:
                        return ParseResult(success=False, error_message=f"Failed to create navigate goal: {e}")
                
                # Check if it's a target
                target = self.target_mappings.get(target_or_direction)
                if target:
                    priority = self._extract_priority(text)
                    
                    try:
                        goal = NavigateGoal(
                            target=target,
                            priority=priority
                        )
                        return ParseResult(success=True, goal=goal, confidence=0.8)
                    except Exception as e:
                        return ParseResult(success=False, error_message=f"Failed to create navigate goal: {e}")
        
        return ParseResult(success=False)
    
    def _try_parse_explore_goal(self, text: str) -> ParseResult:
        """Try to parse an explore goal."""
        for pattern in self.explore_patterns:
            if re.search(pattern, text):
                priority = self._extract_priority(text)
                radius = self._extract_distance(text) or 50  # Default radius
                pattern = "spiral"  # Default pattern
                
                # Check for pattern keywords
                if "random" in text:
                    pattern = "random"
                elif "grid" in text:
                    pattern = "grid"
                
                try:
                    goal = ExploreGoal(
                        area_radius=radius,
                        exploration_pattern=pattern,
                        priority=priority
                    )
                    return ParseResult(success=True, goal=goal, confidence=0.8)
                except Exception as e:
                    return ParseResult(success=False, error_message=f"Failed to create explore goal: {e}")
        
        return ParseResult(success=False)
    
    def _extract_priority(self, text: str) -> Priority:
        """Extract priority from text."""
        for keyword, priority in self.priority_keywords.items():
            if keyword in text:
                return priority
        return Priority.MEDIUM
    
    def _extract_distance(self, text: str) -> Optional[int]:
        """Extract distance/radius from text."""
        # Look for patterns like "50 blocks", "within 100", etc.
        distance_patterns = [
            r"(\d+)\s*blocks?",
            r"within\s+(\d+)",
            r"radius\s+(\d+)",
            r"(\d+)\s*units?",
        ]
        
        for pattern in distance_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_direction(self, text: str) -> Optional[Direction]:
        """Extract preferred direction from text."""
        direction_patterns = [
            r"towards?\s+(north|south|east|west)",
            r"to\s+the\s+(north|south|east|west)",
            r"(north|south|east|west)ward",
        ]
        
        for pattern in direction_patterns:
            match = re.search(pattern, text)
            if match:
                direction_text = match.group(1)
                return self.direction_mappings.get(direction_text)
        
        return None


# Convenience function for quick parsing
def parse_command(text: str) -> ParseResult:
    """Quick function to parse a command string."""
    parser = GoalParser()
    return parser.parse(text)