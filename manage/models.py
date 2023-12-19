"""Core data types and recipe file read."""
from __future__ import annotations
import tomllib
from argparse import Namespace
from copy import deepcopy
from pathlib import Path

from typing import Any, Callable, Dict, Iterable, TypeVar

from pydantic import BaseModel, validator

from manage.utilities import message, smart_join, success, warning


TClass = TypeVar("T")
TStep = TypeVar("Step")
TRecipes = TypeVar("Recipes")
TConfiguration = TypeVar("Configuration")


class Step(BaseModel):
    """A step in a recipe."""

    # FROM inbound manage file:
    method: str | None = None  # Reference to the built-in method to run
    recipe: str | None = None  # Reference to the id_ of another recipe.

    confirm: bool | None = None  # Default value is a function of the respective method
    verbose: bool | None = False
    allow_error: bool | None = False

    arguments: Dict[str, Any] = {}  # Supplemental arguments for the callable

    # NOT from inbound manage file:
    class_: TClass | None = None  # Python method we'll instantiate and call if this is a "method" step.

    @validator("recipe", always=True)
    @classmethod
    def check_consistency(cls, v, field, values):
        """Ensure that EITHER method or another recipe is specified on creation.

        NOTE: We use ~recipe~ here as it's *after* the ~method~ attribute in field definition order!
        """
        if v is None and values["method"] is None:
            raise ValueError("must provide either method or recipe")
        if v is not None and values["method"] is not None:
            raise ValueError("must not provide both method and recipe")
        return v

    def get_arg(self, arg_key: str, default: Any | None = None) -> Any | None:
        """Return the value associated with the specified argument (or None)."""
        return self.arguments.get(arg_key, default)

    def name(self) -> str:
        """Return a description name for this step, i.e. either method or recipe."""
        if self.method:
            return self.method
        return self.recipe

    def reflect_runtime_arguments(self, configuration: TConfiguration, verbose: bool = True) -> str:
        """Update the step based on any/all arguments received on the command-line."""
        # For now, only 2 command-line args can trickle down to individual step execution:
        # 'confirm/no-confirm' and 'verbose':
        if configuration.confirm is not None and self.confirm != configuration.confirm:
            # if verbose:
            #     msg = f"Overriding [italic]confirm[/] in {self.name()} from " \
            #         f"[italic]{self.confirm}[/] to [italic]{configuration.confirm}[/]"
            #     message(msg, color='light_slate_grey', end_success=True)
            self.confirm = configuration.confirm

        if configuration.verbose is not None and self.verbose != configuration.verbose:
            # if verbose:
            #     msg = f"Overriding [italic]verbose[/] in {self.name()} from " \
            #         f"[italic]{self.verbose}[/] to [italic]{configuration.verbose}[/]"
            #     message(msg, color='light_slate_grey', end_success=True)
            self.verbose = configuration.verbose

        # Those arguments that are *specific* to this step:
        # for step_arg, step_arg_value  in self.arguments.items():
        #     # *Do* we potentially have a relevant command-line argument?
        #     if hasattr(configuration, step_arg):
        #         # Yes, what is it?
        #         if (runtime_arg_value := getattr(configuration, step_arg)) is not None:
        #             # Is it different than what the step is configured for now?
        #             if step_arg_value != runtime_arg_value:
        #                 # Yep!, Override it!!
        #                 self.arguments[step_arg] = runtime_arg_value
        #                 msg = f"Overriding: [italic]{step_arg}[/] in {self.name()} from " \
        #                     "[italic]{step_arg_value}[/] to [italic]{runtime_arg_value}[/]"
        #                 message(msg, color='light_slate_grey', end_success=True)

    def as_print(self) -> TStep:
        """Return a 'cleaned-up' copy of this step for printing."""
        step = deepcopy(self)

        # We don't need this for printing..
        delattr(step, "class_")

        # And one of these will be empty!
        if step.method:
            delattr(step, "recipe")
        else:
            delattr(step, "method")

        return step.__dict__


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
        """Is the target provide valid against our current recipes? (on a case-folded basis)."""
        return recipe_target.casefold() in [id_.casefold() for id_ in self.keys()]

    def validate_method_steps(self, method_classes_defined: dict[Callable]) -> list | None:
        """Each step in each recipe needs to be either a "built-in" method or refer to another valid step."""
        return_ = list()
        for id_, recipe in self:
            for step in recipe:
                if step.method:
                    if step.method not in method_classes_defined:
                        return_.append(f"Method: '{step.method}' in recipe={id_} is NOT a valid step method!")
                else:
                    if self.get(step.recipe) is None:
                        return_.append(f"Step: '{step.recipe}' in recipe={id_} can't be found in this file!")
        return return_

    def as_print(self) -> TRecipes:
        """."""
        recipes = deepcopy(self)
        recipes.__root__ = deepcopy(self.__root__)
        for name, recipe in self.__root__.items():
            recipe.steps = [step.as_print() for step in recipe.steps]
            recipes.__root__[name] = recipe
        return recipes


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


class PyProject(BaseModel):
    """Encapsulate a parsed pyproject.toml file.

    Specifically:
    - Two general attributes associated with the current project
    - Two related to this package's configuration.
    """

    version: str | None = None  # Current version string..
    package: str | None = None  # Package name..
    recipes: dict = {}  # These are RAW recipe dicts here!
    parameters: dict = {}

    def get_formatted_list_of_targets(self, supplements: list[str] = []) -> str:
        """Return a comma-delimited list of available recipe targets."""
        targets_recipes = list(self.recipes.keys()) + supplements
        if targets_recipes:
            return ": " + smart_join(sorted(targets_recipes), with_or=True)
        return ""

    def get_target_names_and_descriptions(self) -> list[tuple[str, str]]:
        """Return a list of tuples, each containing recipe name and description."""
        return [(name, definition.get("description", "")) for name, definition in self.recipes.items()]

    def is_valid_target(self, target: str) -> bool:
        """Return true if proposed target name is a valid recipe."""
        return target.casefold() in [recipe.casefold() for recipe in self.recipes.keys()]

    @classmethod
    def factory(cls, path_pyproject: Path) -> PyProject:
        """Do a raw read of the specified pyproject.toml path and returning a instance."""
        message(f"Reading {path_pyproject}")
        raw_pyproject = tomllib.loads(path_pyproject.read_text())
        success()

        # "Parse" our portion of pyproject.toml, ie. "tool"/"manage" into two things:
        # - The set of recipes defined
        # - The set of default configuration/control parameters.
        parameters = dict()
        for name, obj in raw_pyproject.get("tool", {}).get("manage", {}).items():
            if name == "recipes":
                recipes = obj
            else:
                parameters[name] = obj

        # Similarly, parse the *current* package and version we're working with.
        package = None
        if packages := raw_pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
            try:
                # FIXME: For now, use the *first* entry in tool.poetry.packages (even though multiple are allowed)
                package_include = packages[0]
                package = package_include.get("include")
            except IndexError:
                ...
        if package is None:
            warning()
            print("[yellow]No 'packages' entry found under \\[tool.poetry] in pyproject.toml; FYI only.")

        # Similarly, get our current version:
        version = raw_pyproject.get("tool", {}).get("poetry", {}).get("version", None)
        if version is None:
            warning()
            print("[yellow]No version label found entry under \\[tool.poetry] in pyproject.toml; FYI only.")

        # Lastly, we have two "built-in" recipes that we make ALWAYS available, specifically, check and print,
        # Add them in here as well so they'll be treated the same as the user's recipes.
        recipes["print"] = {
            "description": "Show/print recipes defined in pyproject.toml",
            "steps": [{"method": "print", "confirm": False}],
        }
        recipes["check"] = {
            "description": "Check configuration in pyproject.toml",
            "steps": [{"method": "check", "confirm": False}],
        }

        return cls(
            package=package,
            version=version,
            parameters=parameters,
            recipes=recipes,
        )


class Configuration(BaseModel):
    """Configuration/state, primarily (but not solely) from command-line args."""

    verbose: bool | None = None
    help: bool | None = None
    target: str | None = None
    dry_run: bool = True
    confirm: bool | None = None  # If set, override step confirmation instruction appropriately.

    version_: str | None = None  # Note: This is the current version # of the project we're working on!
    version: str | None = None  # " In nice format..

    package_: str | None = None  # "

    _messages_: list[str] = []

    def set_value(self, attr: str, value: any, source: str) -> None:
        """Set the specified attr to the value given with verbosity."""
        setattr(self, attr, value)
        self._messages_.append(f"Setting [italic]{attr}[/] to {value} {source}.")

    def set_version(self, version_raw: str | None) -> None:
        """Set both the version attributes based on that provided from poetry."""
        # Set both "raw" & ncie project versions from the pyproject.toml, eg. 1.2.3 and v1.2.3.
        version_formatted = f"v{version_raw}" if version_raw else ""
        self.configuration.version_ = version_raw
        self.configuration.version = version_formatted

    @classmethod
    def factory(cls, args: Namespace, pyproject: PyProject, test: bool = False, **testing) -> Configuration | None:
        """Create a Configuration object, setting some attrs from pyproject.toml.

        We can either set from args (usual case) or pyproject.toml or from kwargs (primarily for testing).
        """
        ############################################################
        # CREATE our Configuration instance with these values
        ############################################################
        configuration = Configuration(package_=getattr(pyproject, "", ""))
        configuration.set_verion(getattr(pyproject, "version", ""))

        # Resolve the rest of the configuration parameters from pyproject and command-line:
        for attr in ["confirm", "dry_run", "help", "target", "verbose"]:
            configuration = _resolve_parameter(args, attr, pyproject, configuration)

        # Handle special case of "--live" on command-line (and ONLY from command-line!)
        if getattr(args, "live", None):
            configuration.set_value("dry_run", False, "based on --live on command-line")

        # Finally, for testing only, override any other attrs:
        if testing:
            for attr, value in testing.items():
                configuration.set_value(attr, value, "from testing kwargs")

        ############################################################
        # Verbose output to be nice??
        ############################################################
        if configuration.verbose:
            for msg in configuration._messages_:
                message(msg, color="light_slate_grey", end_success=True)
        if test:
            for msg in configuration._messages_:
                print(msg)

        return configuration


def _resolve_parameter(args: Namespace, attr: str, pyproject: PyProject, config: Configuration) -> Configuration:
    """Resolve the specified attribue starting from pyproject and command-line."""
    # First, get from the pyproject.toml:
    if attr in getattr(pyproject, "parameters", []):  # Use getattr to simplify test creation.
        config.set_value(attr, pyproject.parameters[attr], "based on pyproject.toml entry")

    # Then, from command-line args (which *override* pyproject.toml!)
    if value := getattr(args, attr, None):
        msg = "from command-line override" if getattr(config, attr) else "from command-line"
        config.set_value(attr, value, msg)

    return config
