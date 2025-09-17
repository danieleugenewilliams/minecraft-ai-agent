"""
Configuration management for Minecraft AI Agent
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the AI agent"""
    
    def __init__(self, config_path: str = "config/default.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # Use default configuration
            self._config = self._get_default_config()
            self._save_default_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'agent': {
                'name': 'MinecraftAI',
                'update_rate': 0.1,  # seconds
                'max_actions_per_second': 10
            },
            'vision': {
                'screen_region': None,  # Auto-detect Minecraft window
                'image_scale': 0.5,
                'color_space': 'RGB'
            },
            'automation': {
                'click_duration': 0.1,
                'key_press_duration': 0.05,
                'safety_bounds': True
            },
            'ai': {
                'model_type': 'rule_based',  # or 'neural_network'
                'exploration_rate': 0.1,
                'learning_rate': 0.001
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/minecraft_ai.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }
    
    def _save_default_config(self) -> None:
        """Save default configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)