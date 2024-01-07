"""Core data types."""
import tomllib
from pathlib import Path
from typing import Self, TypeVar

from pydantic import BaseModel

from manage import PYPROJECT_PATH
from manage.utilities import msg_debug, msg_failure, msg_warning, smart_join


TConfiguration = TypeVar("TConfiguration")
TPyProject = TypeVar("TPyProject", bound="PyProject")


class PyProject(BaseModel):
    """Encapsulate a parsed pyproject.toml file.

    Specifically:
    - Two general attributes associated with the current project
    - Two related to this package's configuration.
    """

    # fmt: off
    version: str  | None = None  # Current version string..
    package: str  | None = None  # Package name..
    recipes: dict | None = None  # These are RAW recipe dicts here!
    # fmt: on

    def get_formatted_list_of_targets(self, supplements: list[str] = []) -> str:
        """Return a comma-delimited list of available recipe targets."""
        targets_recipes = list(self.recipes.keys()) + supplements
        if targets_recipes:
            return smart_join(sorted(targets_recipes), with_or=True)
        return ""

    def get_target_names_and_descriptions(self) -> list[tuple[str, str]]:
        """Return a list of tuples, each containing recipe name and description."""
        if not self.recipes:
            return []
        else:
            return [(name, definition.get("description", "")) for name, definition in self.recipes.items()]

    def is_valid_target(self, target: str) -> bool:
        """Return true if proposed target name is a valid recipe."""
        return target.casefold() in [recipe.casefold() for recipe in self.recipes.keys()]

    def validate(self) -> bool:
        """Return True is everything's OK with our pyproject object."""
        # Do we have any recipes?
        if not self.recipes:
            msg_failure("No recipes found in 'tool.manage.recipes?")
            return False

        # WARNING: Does our current package have a current version number? (eg. for build/release mgmt.)
        if not self.version:
            msg_warning("FYI, no version label in pyproject.toml's \\[tool.poetry] section.")

        return True

    @classmethod
    def factory(cls, path_pyproject: Path = PYPROJECT_PATH, debug: bool = False) -> Self:
        """Read and instantiate a PyProject instance from teh specified pyproject.toml path."""
        raw_pyproject = tomllib.loads(path_pyproject.read_text())
        if debug:
            msg_debug(f"Successfully read/re-read {path_pyproject}")
        return PyProject.factory_from_raw(raw_pyproject)

    @classmethod
    def factory_from_raw(cls, raw_pyproject: dict) -> Self:
        """Convert the raw_pyproject dict provided (from pyproject.toml) and return an instance."""
        parms = {}

        ################################################################################
        # Actual recipes!
        ################################################################################
        parms["recipes"] = raw_pyproject.get("tool", {}).get("manage", {}).get("recipes", {})

        # *Current* version of it (note, might very likely be null if user isn't managing a formal package!)
        parms["version"] = raw_pyproject.get("tool", {}).get("poetry", {}).get("version", None)

        return PyProject(**parms)
