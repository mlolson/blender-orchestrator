"""API key and configuration management for AI providers."""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    """Configuration for a single AI provider."""
    api_key: str
    base_url: Optional[str] = None
    timeout: int = 300  # 5 minutes default
    max_retries: int = 3
    default_model: Optional[str] = None
    extra: Dict = field(default_factory=dict)


class AIConfig:
    """Manages AI provider configuration.

    Configuration is loaded from:
    1. Environment variables (highest priority)
    2. Config file at ~/.config/blender-mcp/ai_providers.json
    """

    def __init__(self):
        self._configs: Dict[str, ProviderConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from environment and config file."""
        # Load from environment variables first
        self._load_from_env()

        # Then load from config file (won't override env vars)
        config_paths = [
            Path.home() / ".config" / "blender-mcp" / "ai_providers.json",
            Path.home() / ".blender-mcp" / "ai_providers.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                self._load_from_file(config_path)
                break

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Meshy (primary mesh generation)
        meshy_key = os.getenv("MESHY_API_KEY")
        if meshy_key:
            self._configs["meshy"] = ProviderConfig(
                api_key=meshy_key,
                base_url="https://api.meshy.ai/openapi/v2",
                timeout=600,  # 10 min for mesh generation
                default_model="latest",
            )

        # Stability AI
        stability_key = os.getenv("STABILITY_API_KEY")
        if stability_key:
            self._configs["stability"] = ProviderConfig(
                api_key=stability_key,
                base_url="https://api.stability.ai",
                timeout=300,
                default_model="stable-fast-3d",
            )

        # OpenAI (optional, for DALL-E image generation)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self._configs["openai"] = ProviderConfig(
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                timeout=120,
                default_model="dall-e-3",
            )

    def _load_from_file(self, path: Path):
        """Load additional configuration from JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)

            for provider, config_data in data.items():
                # Don't override existing env-based configs
                if provider not in self._configs:
                    if isinstance(config_data, dict) and "api_key" in config_data:
                        self._configs[provider] = ProviderConfig(
                            api_key=config_data["api_key"],
                            base_url=config_data.get("base_url"),
                            timeout=config_data.get("timeout", 300),
                            max_retries=config_data.get("max_retries", 3),
                            default_model=config_data.get("default_model"),
                            extra=config_data.get("extra", {}),
                        )
        except (json.JSONDecodeError, IOError) as e:
            # Log but don't fail on config file errors
            print(f"Warning: Could not load AI config from {path}: {e}")

    def get_config(self, provider: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider.

        Args:
            provider: Provider name (replicate, stability, openai)

        Returns:
            ProviderConfig if configured, None otherwise
        """
        return self._configs.get(provider)

    def has_provider(self, provider: str) -> bool:
        """Check if a provider is configured.

        Args:
            provider: Provider name

        Returns:
            True if provider has valid configuration
        """
        return provider in self._configs

    def list_providers(self) -> list:
        """List all configured provider names.

        Returns:
            List of provider names with valid configuration
        """
        return list(self._configs.keys())

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider.

        Args:
            provider: Provider name

        Returns:
            API key string or None
        """
        config = self._configs.get(provider)
        return config.api_key if config else None


# Global singleton instance
_config: Optional[AIConfig] = None


def get_ai_config() -> AIConfig:
    """Get the global AI configuration instance.

    Returns:
        AIConfig singleton instance
    """
    global _config
    if _config is None:
        _config = AIConfig()
    return _config


def reset_ai_config():
    """Reset the global config (useful for testing)."""
    global _config
    _config = None
