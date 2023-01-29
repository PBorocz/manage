"""Core data types and recipe toml read"""
from typing import Callable, Iterable

from pydantic import BaseModel


class Step(BaseModel):
    action: str
    confirm: bool | None = True
    echo_stdout: bool | None = False
    allow_error: bool | None = False
    quiet_mode: bool | None = False
    callable_: Callable | None = None  # Python func we'll call if this is a "method" step.

    # NOTE: We can't perform simple pydantic validation on 'action' here until we have a list of methods,
    # so...we do it with a dedicated method on the recipes instance


class Recipe(BaseModel):
    description: str | None = None
    steps: list[Step] = []

    def __iter__(self):
        return iter(self.steps)

    def __len__(self):
        return len(self.steps)


class Recipes(BaseModel):
    __root__: dict[str, Recipe]

    def __len__(self):
        return len(self.__root__)

    def items(self) -> Iterable[tuple[str, Recipe]]:
        return iter(self.__root__.items())

    def get(self, id_: str) -> Recipe | None:
        return self.__root__.get(id_.casefold())

    def set(self, id_: str, recipe: Recipe) -> None:
        self.__root__[id_] = recipe

    def keys(self) -> Iterable[str]:
        return iter(self.__root__.keys())

    def ids(self) -> list[str]:
        """Return a sorted list of recipe "ids", used for command-line argument for what to run"""
        return sorted(list(self.keys()))  # in self if not recipe.id_.startswith("__")])

    def check_target(self, recipe_target: str) -> bool:
        """Is the target provide valid against our current recipes?"""
        targets_defined_casefolded = [id_.casefold() for id_ in self.keys()]
        return recipe_target.casefold() in targets_defined_casefolded

    def validate_step_actions(self, methods_available: dict[Callable]) -> list | None:
        """Each step in each recipe needs to be either a "built-in" method or refer to another step"""
        return_ = list()
        for id_, recipe in self.items():
            for step in recipe:
                # Is this step a method-type?
                if step.action in methods_available:
                    continue
                else:
                    # Then, better be another step!
                    if self.get(step.action) is None:
                        return_.append(f"Sorry, {step.action} in {id_} is NOT valid!")
        return return_


class Configuration(BaseModel):
    version_: str | None = None
    package: str | None = None

    def version(self):
        """Return version number in "formal" format, usable (for instance) as git tag."""
        return f"v{self._version}"
