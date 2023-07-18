"""Core data types and recipe file read."""
import argparse
from typing import Any, Callable, Dict, Iterable, TypeVar

from pydantic import BaseModel, validator

from manage.utilities import get_package_version_from_pyproject_toml, message


TStep = TypeVar("Step")
TConfiguration = TypeVar("Configuration")


class Step(BaseModel):
    """A step in a recipe."""
    # FROM inbound manage file:
    method: str | None = None   # Reference to the built-in method to run
    recipe: str | None = None   # Reference to the id_ of another recipe.

    confirm: bool | None = True
    echo_stdout: bool | None = False
    allow_error: bool | None = False
    quiet_mode: bool | None = False
    arguments: Dict[str, Any] = {}   # Supplemental arguments for the callable

    # NOT from inbound manage file:
    callable_: Callable | None = None  # Python func we'll call if this is a "method" step.

    @validator('recipe', always=True)
    def check_consistency(cls, v, field, values):
        """Ensure that EITHER method or another recipe is specified on creation.

        NOTE: We use ~recipe~ here as it's *after* the ~method~ attribute in field definition order!
        """
        if v is not None and values['method'] is not None:
            raise ValueError('must not provide both method and recipe')
        if v is None and values['method'] is None:
            raise ValueError('must provide either method or recipe')
        return v

    def get_arg(self, arg_key: str) -> Any | None:
        """Return the value associated with the specified argument (or None)."""
        return self.arguments.get(arg_key)

    def name(self) -> str:
        """Return a description name for this step, i.e. either method or recipe."""
        if self.method:
            return self.method
        return self.recipe

    def reflect_runtime_arguments(self, args: argparse.Namespace) -> str:
        """Update the step based on any/all arguments received on the command-line."""
        # Common across all steps (for now, just the "confirm" flag):
        if args.confirm is not None:

            # Is the command-line setting DIFFERENT than that for the step?
            if self.confirm != args.confirm:
                # FIXME: Verbose only?
                msg = f"Overriding [italic]confirm[/] in {self.name()} from " \
                    "[italic]{self.confirm}[/] to [italic]{args.confirm}[/]"
                message(msg, color='light_slate_grey', end_success=True)
                self.confirm = args.confirm

        # Those arguments that are *specific* to this step:
        for step_arg, step_arg_value  in self.arguments.items():
            # *Do* we potentially have a relevant command-line argument?
            if hasattr(args, step_arg):
                # Yes, what is it?
                if (runtime_arg_value := getattr(args, step_arg)) is not None:
                    # Is it different than what the step is configured for now?
                    if step_arg_value != runtime_arg_value:
                        # Yep!, Override it!!
                        self.arguments[step_arg] = runtime_arg_value
                        # FIXME: Verbose only?
                        msg = f"Overriding: [italic]{step_arg}[/] in {self.name()} from " \
                            "[italic]{step_arg_value}[/] to [italic]{runtime_arg_value}[/]"
                        message(msg, color='light_slate_grey', end_success=True)


class Recipe(BaseModel):
    """A recipe, consisting of a description and a set of steps."""
    description: str | None = None
    steps: list[Step] = []

    def __iter__(self):
        return iter(self.steps)

    def __len__(self):
        return len(self.steps)


class Recipes(BaseModel):
    """A collection of recipes, maps 1-to-1 with an inbound file."""
    __root__: dict[str, Recipe]

    def __len__(self):
        return len(self.__root__)

    def __iter__(self) -> Iterable[tuple[str, Recipe]]:
        return iter(self.__root__.items())

    def get(self, id_: str) -> Recipe | None:
        """Treat Recipes as a mapping, return a specific Recipe by it's id."""
        return self.__root__.get(id_.casefold())

    def set(self, id_: str, recipe: Recipe) -> None:
        """Treat Recipes as a mapping, setting a specific Recipe using it's id."""
        self.__root__[id_] = recipe

    def keys(self) -> Iterable[str]:
        """Get the names of all Recipes."""
        return iter(self.__root__.keys())

    def ids(self) -> list[str]:
        """Return a sorted list of recipe "ids", used for command-line argument for what to run."""
        return sorted(list(self.keys()))  # in self if not recipe.id_.startswith("__")])

    def check_target(self, recipe_target: str) -> bool:
        """Is the target provide valid against our current recipes?"""
        targets_defined_casefolded = [id_.casefold() for id_ in self.keys()]
        return recipe_target.casefold() in targets_defined_casefolded

    def validate_methods_steps(self, methods_available: dict[Callable]) -> list | None:
        """Each step in each recipe needs to be either a "built-in" method or refer to another valid step."""
        return_ = list()
        for id_, recipe in self:
            for step in recipe:
                if step.method:
                    if step.method not in methods_available:
                        return_.append(f"Method: '{step.method}' in recipe={id_} is NOT a valid step method!")
                else:
                    if self.get(step.recipe) is None:
                        return_.append(f"Step: '{step.recipe}' in recipe={id_} can't be found in this file!")
        return return_


class Argument(BaseModel):
    """Possible argument for a method."""
    name: str
    type_: type
    default: Any | None = None


class Arguments(BaseModel):
    """Collection of Arguments for a method."""
    arguments: list[Argument] = []

    def get_argument(self, argument_name: str) -> Argument | None:
        """Lookup Argument by name."""
        for arg in self.arguments:
            if arg.name == argument_name:
                return arg
        return None


class Configuration(BaseModel):
    """Internal configuration/state."""
    version_: str | None = None
    package_: str | None = None

    def version(self):
        """Return version number in "formal" format, usable (for instance) as git tag."""
        return f"v{self.version_}"


def configuration_factory(args) -> Configuration | None:
    """Create a Configuration object, setting some attrs from pyproject.toml."""
    version, package = get_package_version_from_pyproject_toml()
    return Configuration(version_=version, package_=package)
