"""Core Data Types"""
from typing import Callable

from pydantic import BaseModel, validator


class Step(BaseModel):
    method: str | None = None
    step: str | None = None
    confirm: bool | None = True
    echo_stdout: bool | None = False
    allow_error: bool | None = False
    quiet_mode: bool | None = False
    callable_: Callable | None = None  # Python func we'll call if this is a "method" step.

    @validator('method', 'step')
    def validate_one_field_using_the_others(cls, value, values, field, config):
        # TEST: ALL 4 cases possible here
        if field.name == "method":
            # Pass this through as is and check on the "step" field next time through
            return value
        elif field.name == "step":
            if value is None and values.get("method") is None:
                raise ValueError("Either 'method' or 'step' must be specified for a recipe step.")
            elif value and values["method"]:
                raise ValueError("Only one of 'method' or 'step' must be specified for a recipe step, not both.")
            return value


class Recipe(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: list[Step] = []

    def __iter__(self):
        return iter(self.steps)


class Recipes(BaseModel):
    recipes: dict[str, Recipe]

    def __iter__(self):
        return iter(self.recipes.items())

    def __getitem__(self, id_: str) -> Recipe | None:
        return self.recipes.get(id_.casefold())

    def ids(self) -> list[str]:
        """Return a sorted list of recipe "ids", used for command-line argument for what to run"""
        return sorted(list(self.recipes.keys()))  # in self if not recipe.id_.startswith("__")])

    def check_target(self, recipe_target: str) -> bool:
        """Is the target provide valid against our current recipes?"""
        targets_defined_casefolded = [id_.casefold() for id_ in self.recipes.keys()]
        return recipe_target.casefold() in targets_defined_casefolded


class Configuration(BaseModel):
    version_: str | None = None
    package: str | None = None

    def version(self):
        """Return version number in "formal" format, usable (for instance) as git tag."""
        return f"v{self._version}"
