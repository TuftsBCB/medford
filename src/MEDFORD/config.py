"""
Configuration file locator for MEDFORD.

This module handles finding static configuration files (like medford.mvd)
in both development and installed modes.

The approach uses the module's __file__ attribute to locate the package root,
then finds the conf/ directory relative to it.
"""

import os
from pathlib import Path
from typing import Optional


def get_package_root() -> Path:
    return Path(__file__).parent


def get_config_dir() -> Path:
    config_dir = get_package_root() / "conf"

    if not config_dir.exists():
        raise FileNotFoundError(
            f"Configuration directory not found: {config_dir}\n"
            f"Expected to find it at: {config_dir.absolute()}\n"
            "This may indicate an installation problem."
        )

    return config_dir


def get_config_file(filename: str) -> Path:
    config_path = get_config_dir() / filename

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {filename}\n"
            f"Looked in: {config_path.absolute()}\n"
            f"Available files in config dir: {list(get_config_dir().iterdir())}"
        )

    return config_path


def find_config_file(filename: str, fallback_search: bool = False) -> Optional[Path]:
    try:
        # First, try the package conf directory
        return get_config_file(filename)
    except FileNotFoundError:
        if fallback_search:
            # Fallback: check current working directory (for development)
            cwd_path = Path.cwd() / filename
            if cwd_path.exists():
                if __debug__:
                    print(f"DEBUG: Using config file from current directory: {cwd_path}")
                return cwd_path

        # If we get here, file wasn't found anywhere
        return None


def get_validator_config() -> Path:
    return get_config_file("medford.mvd")
