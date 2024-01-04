"""Probably the closest thing we have to "constants"."""
from pathlib import Path

# FIXME?: Assume's we're always running from top-level/project directory!
PYPROJECT_PATH = Path.cwd() / "pyproject.toml"

# DO NOT CHANGE: Version string here WILL be kept up to date on poetry_version_sync method:
__version__ = "0.3.2"
