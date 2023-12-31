"""Core data types."""
from typing import Self, TypeVar

from pydantic import BaseModel

from manage.utilities import msg_failure, msg_warning, smart_join


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
            return ": " + smart_join(sorted(targets_recipes), with_or=True)
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

        # WARNING: Do we have the name of the current package we're processing (eg. for builds etc.)
        if self.package is None:
            msg_warning("No 'packages' entry found in \\[tool.poetry] in pyproject.toml; FYI only.")

        # WARNING: Does our current package have a current version number? (eg. for build/release mgmt.)
        if not self.version:
            msg_warning("No version label found in \\[tool.poetry] in pyproject.toml; FYI only.")

        return True

    @classmethod
    def factory(cls, raw_pyproject: dict) -> Self:
        """Use the raw_pyproject dict from pyproject.toml path and return a instance."""
        instance = PyProject()

        # Actual recipes!
        instance.recipes = raw_pyproject.get("tool", {}).get("manage", {}).get("recipes", {})

        # OPTIONAL: Parse "main" portion of pyproject.toml to find the *current* package the user want's management for:
        if packages := raw_pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
            try:
                # FIXME: For now, use the *first* entry in tool.poetry.packages (even though multiple are allowed)
                package_include = packages[0]
                instance.package = package_include.get("include")
            except IndexError:
                ...

        # OPTIONAL: Get the current version of it from the main portion of the pyproject file:
        instance.version = raw_pyproject.get("tool", {}).get("poetry", {}).get("version", None)

        # Done!
        return instance
