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
    id_: str
    name: str | None = None
    description: str | None = None
    steps: list[Step] = []

    def __iter__(self):
        for step in self.steps:
            yield step


class Recipes(BaseModel):
    recipes: list[Recipe]

    def __iter__(self):
        for recipe in self.recipes:
            yield recipe

    def find_recipe(self, id_: str) -> Recipe | None:
        """Return the recipe with the associated id or None if not found."""
        for recipe in self:
            if id_.casefold() == recipe.id_.casefold():
                return recipe
        return None

    def ids(self):
        """Return a sorted list of recipe "ids", used for command-line argument for what to run"""
        return sorted([recipe.id_ for recipe in self])  # in self if not recipe.id_.startswith("__")])

    def check_target(self, recipe_target: str) -> bool:
        """Is the target provide valid against our current recipes?"""
        return recipe_target.casefold() in [recipe.id_.casefold() for recipe in self]


class Configuration(BaseModel):
    version_: str | None = None
    package: str | None = None

    def version(self):
        """Return version number in "formal" format, usable (for instance) as git tag."""
        return f"v{self._version}"
