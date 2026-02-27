"""Configuration loader for YAML files."""

import yaml
from pathlib import Path
from typing import Any, Dict


class ConfigLoader:
    """Load and manage YAML configuration."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports nested keys with dots)."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def polling(self) -> Dict[str, Any]:
        """Get polling configuration."""
        return self._config.get('polling', {})
    
    @property
    def filters(self) -> Dict[str, Any]:
        """Get filter configuration."""
        return self._config.get('filters', {})
    
    @property
    def summarization(self) -> Dict[str, Any]:
        """Get summarization configuration."""
        return self._config.get('summarization', {})
    
    @property
    def notifications(self) -> Dict[str, Any]:
        """Get notifications configuration."""
        return self._config.get('notifications', {})


# Global config instance
_config_instance = None


def get_config() -> ConfigLoader:
    """Get or create config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
