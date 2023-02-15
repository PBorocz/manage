"""Setup functions, not meant for direct calling from recipe file."""
import importlib
import sys
from pathlib import Path
from typing import Callable, Final

import yaml
from rich import print

from manage import steps as step_module
from manage.models import Configuration, Recipes, Recipe, Step
from manage.utilities import fmt, success, failure, SimpleObj


def read_recipe_file(path_recipes: Path) -> dict:
    """Do a raw read of the specified recipe file path, doing no other processing!."""
    print(fmt(f"Reading recipes ({path_recipes})", color='blue'), flush=True, end="")
    if not path_recipes.exists():
        failure()
        print(f"[red]Sorry, unable to find {path_recipes} for recipes.")
        sys.exit(1)

    # Read raw (safely!)...
    return yaml.safe_load(path_recipes.read_text())


def parse_recipe_file(args: SimpleObj, raw_recipes: dict, methods: dict[Callable] | None) -> Recipes:
    """We want a clean/easy-to-use recipe file, thus, do our own deserialisation."""

    # ..and deserialise into our types dataclasses:
    d_recipes = dict()
    if raw_recipes:
        for id_, raw_recipe in raw_recipes.items():
            recipe = Recipe(**raw_recipe)
            d_recipes[id_] = recipe
        success()

    # Convert raw objects into typed hierarchy.
    recipes = Recipes.parse_obj(d_recipes)

    # Add system recipe target(s)
    recipes = _add_system_recipe_s(recipes)

    # Override any recipe settings with anything from the command-line:
    recipes = _override_steps_from_args(recipes, args)

    if methods:
        # Map the built-in methods available onto each recipe step.
        recipes = _add_callables(recipes, methods)

        # Validate that each of the methods are valid.
        if not _validate_recipe_methods(recipes, methods):
            sys.exit(1)

    return recipes


def validate_existing_version_numbers(configuration: Configuration) -> bool:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml"""

    def __get_last_release_from_readme() -> str:
        """Mini state-machine to find last "release" in our changelog embedded within our README."""
        path_readme = Path.cwd() / "README.md"
        header = "###"
        if not path_readme.exists():
            path_readme = Path.cwd() / "README.org"
            header = "***"
            if not path_readme.exists():
                print(f"[red]Sorry, unable to open EITHER README.md or README.org from the current directory.")
                return None

        unreleased_header = f"{header} Unreleased"
        take_next_release = False
        for line in path_readme.read_text().split("\n"):
            if line.startswith(unreleased_header):
                take_next_release = True
                continue
            if take_next_release and line.startswith(header):  # eg "*** vX.Y.Z - <aDate>"
                tag = line.split()[1]
                version = tag[1:]
                return version
        return None

    msg = fmt("Checking consistency of versions (pyproject.toml & README)", color='blue')
    print(msg, end="", flush=True)
    last_release_version = __get_last_release_from_readme()
    if last_release_version != configuration.version_:
        failure()
        print(f"[red]Warning, pyproject.toml has version: {configuration.version_} "
              f"while last release in README is {last_release_version}!")
        return False
    success()
    return True


def _validate_recipe_methods(recipes: Recipes, step_methods: dict[str, Callable]) -> bool:
    """Make sure all the the methods and steps from our recipes are defined and available"""
    print(fmt("Validating recipes", color='blue'), flush=True, end="")
    if invalid_method_steps := recipes.validate_methods_steps(step_methods):
        print("\n[red]Sorry, we encountered the following errors in inbound recipe file:")
        for method_step in invalid_method_steps:
            print(f"[red]- {method_step}")
        failure()
        return False
    success()
    return True


def _add_callables(recipes: Recipes, step_methods: dict[str, Callable]) -> Recipes:
    """Add the "callable" method onto each method step to dispatch on."""
    for name, recipe in recipes:
        for step in recipe:
            if callable_ := step_methods.get(step.method):
                step.callable_ = callable_
    return recipes


def _add_system_recipe_s(recipes: Recipes) -> Recipes:
    """Embellish recipes with our "built-in" one(s)."""
    recipes.set(
        "check",
        Recipe(description="Check configuration only.", steps=[Step(method="check", confirm=False,),]))
    recipes.set(
        "show",
        Recipe(description="Show recipe file contents.", steps=[Step(method="show", confirm=False,)]))
    return recipes


def _override_steps_from_args(recipes: Recipes, args: SimpleObj) -> Recipes:
    """Override any recipe settings with anything from the command-line."""
    for name, recipe in recipes:
        for step in recipe:
            if args.no_confirm == True:
                # We ARE overriding confirm, is this a case where step.confirm is set?
                if step.confirm:
                    step.confirm = False  # Yes..
                    print(fmt(f"Overriding confirmation: {name} - {step.name()}", color='yellow'), flush=True, end="")
                    success(color="yellow")
    return recipes


def simple_gather_available_steps() -> dict[str, Callable]:
    print(fmt("Reading recipe steps available", color='blue'), flush=True, end="")
    return_ = dict()
    for method_name, method in vars(step_module).items():
        if not method_name.startswith("__"):
            return_[method_name] = method
    if not return_:
        failure()
        print("[red]Unable to find any valid command steps in manage/commands/*.py?")
        sys.exit(1)
    success()
    return return_


def gather_available_steps() -> dict[str, Callable]:
    """Read and return all the python-defined step methods available"""

    def __gather_step_modules():
        """Utility method that iterates over all step modules."""
        for path in sorted((Path(__file__).parent / Path("steps")).glob("*.py")):
            if path.name.startswith("__"):
                continue
            module = importlib.import_module(f"manage.steps.{path.stem}")
            yield path.stem, getattr(module, "main")

    print(fmt("Reading recipe steps available", color='blue'), flush=True, end="")

    # Get all the 'main" methods in each python file in the steps module:
    return_ = {method_name: method for method_name, method in __gather_step_modules()}

    if not return_:
        failure()
        print("[red]Unable to find any valid command steps in manage/steps/*.py?")
        sys.exit(1)
    success()
    return return_
