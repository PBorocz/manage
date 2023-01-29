"""Core data types and recipe file read"""
from typing import Callable, Iterable

from pydantic import BaseModel, validator


class Step(BaseModel):
    method: str | None = None
    step: str | None = None
    confirm: bool | None = True
    echo_stdout: bool | None = False
    allow_error: bool | None = False
    quiet_mode: bool | None = False
    callable_: Callable | None = None  # Python func we'll call if this is a "method" step.

    # Confirm that EITHER method or step is specified on creation.
    # NOTE: We use "step" here as it's *after* method in field definition order!
    @validator('step', always=True)
    def check_consistency(cls, v, field, values):
        # print(f"check_consistency: {v=} {field.name=} {values=}")
        if v is not None and values['method'] is not None:
            raise ValueError('must not provide both method and step')
        if v is None and values['method'] is None:
            raise ValueError('must provide either method or step')
        return v

    # NOTE: We can't perform DYNAMIC validation on 'method' here until we have a list of methods,
    # so, we do it with a dedicated method on the recipes instance


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

    def validate_methods_steps(self, methods_available: dict[Callable]) -> list | None:
        """Each step in each recipe needs to be either a "built-in" method or refer to another valid step"""
        return_ = list()
        for id_, recipe in self.items():
            for step in recipe:
                if step.method:
                    if step.method not in methods_available:
                        return_.append(f"Method: '{step.method}' in recipe={id_} is NOT a valid step method!")
                else:
                    if self.get(step.step) is None:
                        return_.append(f"Step: '{step.step}' in recipe={id_} can't be found in this file!")
        return return_


class Configuration(BaseModel):
    version_: str | None = None
    package: str | None = None

    def version(self):
        """Return version number in "formal" format, usable (for instance) as git tag."""
        return f"v{self.version_}"
