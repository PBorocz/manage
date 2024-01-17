"""Probably the closest thing we have to "constants"."""
from pathlib import Path

# FIXME?: Assume's we're always running from top-level/project directory!
PYPROJECT_PATH = Path.cwd() / "pyproject.toml"

# DO NOT CHANGE: Version string here WILL be kept in-sync with pyproject.toml using poetry-bumpversion plugin!
__version__ = "0.3.6"
