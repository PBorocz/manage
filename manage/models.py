"""Core data types and recipe file read."""
from __future__ import annotations
import tomllib
from argparse import Namespace
from copy import deepcopy
from pathlib import Path

from typing import Any, Dict, Iterable, TypeVar

from pydantic import BaseModel, validator

from manage.utilities import message, smart_join


TClass = TypeVar("Class")
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
            if verbose:
                msg = (
                    f"(- (overriding [italic]confirm[/] in {self.name()} from "
                    f"[italic]{self.confirm}[/] to [italic]{configuration.confirm}[/])"
                )
                message(msg, color="light_slate_grey", end_success=True)
            self.confirm = configuration.confirm

        if configuration.verbose is not None and self.verbose != configuration.verbose:
            if verbose:
                msg = (
                    f"- (overriding [italic]verbose[/] in {self.name()} from "
                    f"[italic]{self.verbose}[/] to [italic]{configuration.verbose}[/])"
                )
                message(msg, color="light_slate_grey", end_success=True)
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
        return iter(sorted(self.__root__.keys()))

    def check_target(self, recipe_target: str) -> bool:
        """Is the target provide valid against our current recipes? (on a case-folded basis)."""
        return recipe_target.casefold() in [id_.casefold() for id_ in self.keys()]

    def as_print(self) -> TRecipes:
        """."""
        recipes = deepcopy(self)
        recipes.__root__ = deepcopy(self.__root__)
        for name, recipe in self.__root__.items():
            recipe.steps = [step.as_print() for step in recipe.steps]
            recipes.__root__[name] = recipe
        return recipes

    def laminate_method_classes(self, configuration: Configuration, method_classes: dict[str, TClass] | None) -> None:
        """Add the instantiable class onto each method step to dispatch from (only not in testing..).

        We already validated that all the recipes are valid, this just ties them classes
        to the steps for actual execution.
        """
        if method_classes:
            for name, recipe in self:
                for step in recipe:
                    step.class_ = method_classes.get(step.method)

    @classmethod
    def factory(cls, configuration: Configuration, pyproject: PyProject) -> Recipes:
        """We want a clean/easy-to-use recipe file, thus, do our own deserialisation and embellishment."""
        d_recipes = {id_: Recipe(**raw_recipe) for id_, raw_recipe in pyproject.recipes.items()}
        return cls.parse_obj(d_recipes)


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

    # fmt: off
    version: str  | None = None  # Current version string..
    package: str  | None = None  # Package name..
    recipes: dict | None = None  # These are RAW recipe dicts here!
    #
    # NOTE: These are the ONLY place we're set set the default values
    #       for "verbose", "live", "dry-run" and "confirm"
    #       command-line parameters unless they're NOT set/available
    #       from the pyproject.toml file:
    #
    cli_defaults: dict = {
        "default_verbose" : False,
        "default_confirm" : False,
        "default_dry_run" : True,
        "default_live"    : False,
    }
    # fmt: on

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

    def get_parm(self, parm: str) -> bool:
        """Return the value associated with the parameter name specified."""
        return self.cli_defaults.get(parm)

    @classmethod
    def factory(cls, path_pyproject: Path) -> PyProject:
        """Do a raw read of the specified pyproject.toml path and returning a instance."""
        raw_pyproject = tomllib.loads(path_pyproject.read_text())

        instance = PyProject()
        ################################################################################
        # Parse "our" portion of pyproject.toml, ie. [tool.manage] into two things:
        # - The set of default configuration/control cli_defaults.
        # - The set of recipes defined.
        ################################################################################
        for name, value in raw_pyproject.get("tool", {}).get("manage", {}).items():
            if name == "recipes":
                instance.recipes = value
            else:
                if name not in instance.cli_defaults:
                    message(
                        f"Unexpected setting found in 'tool.manage' section: {name}, please check!",
                        color="red",
                        end_warning=True,
                    )
                else:
                    if instance.cli_defaults[name] != value:
                        message(
                            f"- (overriding internal default for [italic]{name}[/] "
                            f"from {instance.cli_defaults[name]} to {value})",
                            color="light_slate_grey",
                            end_success=True,
                        )
                    instance.cli_defaults[name] = value

        ################################################################################
        # Do validity/consistency checking
        ################################################################################
        if instance.cli_defaults.get("default_dry_run") == instance.cli_defaults.get("default_live"):
            message(
                "You shouldn't set both 'dry_run' and 'live' to the same value in 'tool.manage', please check!",
                color="red",
                end_warning=True,
            )

        ################################################################################
        # Parse the *current* package:
        ################################################################################
        if packages := raw_pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
            try:
                # FIXME: For now, use the *first* entry in tool.poetry.packages (even though multiple are allowed)
                package_include = packages[0]
                instance.package = package_include.get("include")
            except IndexError:
                ...
        if instance.package is None:
            message(
                "No 'packages' entry found under \\[tool.poetry] in pyproject.toml; FYI only.",
                color="yellow",
                end_warning=True,
            )

        ################################################################################
        # And get the current version of it:
        ################################################################################
        version = raw_pyproject.get("tool", {}).get("poetry", {}).get("version", None)
        if not version:
            message(
                "No version label found entry under \\[tool.poetry] in pyproject.toml; FYI only.",
                color="yellow",
                end_warning=True,
            )
        else:
            instance.version = version

        ################################################################################
        # Lastly, we have two "built-in" recipes that we make ALWAYS
        # available, specifically, 'check' and 'print', Add them in
        # here as well so they'll be treated the same as the user's
        # recipes.
        ################################################################################
        instance.recipes["print"] = {
            "description": "Show/print recipes defined in pyproject.toml",
            "steps": [{"method": "print", "confirm": False}],
        }
        instance.recipes["check"] = {
            "description": "Check configuration of pyproject.toml",
            "steps": [{"method": "check", "confirm": False}],
        }

        # Done!
        return instance


class Configuration(BaseModel):
    """Configuration/state, primarily (but not solely) obo command-line args."""

    # fmt: off
    help       : bool | None = None  # Were we requested to just display help?
    verbose    : bool | None = None  # Are we running in overall verbose mode?
    target     : str  | None = None  # What is the target to be performed?
    confirm    : bool | None = None  # Should we perform confirmations on steps?
    dry_run    : bool | None = None  # Are we running in dry-run mode (True) or live mode (False)

    version_   : str  | None = None  # Note: This is the current version # of the project we're working on!
    version    : str  | None = None  # " In nice format..
    package_   : str  | None = None  # "
    _messages_ : list[str] = []
    # fmt: on

    def set_value(self, attr: str, value: any, source: str) -> None:
        """Set the specified attr to the value given with verbosity."""
        setattr(self, attr, value)
        self._messages_.append(f"- (setting [italic]{attr}[/] to {value} {source})")

    def set_version(self, version_raw: str | None) -> None:
        """Set both the version attributes based on that provided from poetry."""
        version_formatted = f"v{version_raw}" if version_raw else ""
        self.version_ = version_raw
        self.version = version_formatted

    @classmethod
    def factory(cls, args: Namespace, pyproject: PyProject, test: bool = False, **kwargs) -> Configuration | None:
        """Create a Configuration object, setting some attrs from pyproject.toml.

        We can either set from args (usual case) or pyproject.toml or from kwargs (primarily for testing).
        """
        ############################################################
        # CREATE our Configuration instance with these values
        ############################################################
        configuration = Configuration(package_=getattr(pyproject, "", ""))
        configuration.set_version(getattr(pyproject, "version", ""))

        # Get the rest of the command-line parameters (whose default
        # values could have come from pyproject.toml!)
        for attr in ["confirm", "verbose", "help", "target"]:
            setattr(configuration, attr, getattr(args, attr))

        # Handle special case of "--live" on command-line (and ONLY from command-line!)
        if getattr(args, "live", None):
            configuration.set_value("dry_run", False, "based on --live on command-line")

        # Finally, for testing only, override any other attrs:
        if kwargs:
            for attr, value in kwargs.items():
                configuration.set_value(attr, value, "from (testing) kwargs")

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
