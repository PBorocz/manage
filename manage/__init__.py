"""Probably the closest thing we have to "constants"."""
from pathlib import Path

# FIXME?: Assume's we're always running from top-level/project directory!
DEFAULT_PROJECT_PATH = Path.cwd() / "pyproject.toml"
