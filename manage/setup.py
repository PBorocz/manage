"""Setup functions, not meant for direct calling from recipe file."""
import sys
from pathlib import Path
from typing import Callable, Final

import yaml
from rich import print

from manage import steps as step_module
from manage.models import Configuration, Recipes, Recipe, Step
from manage.utilities import fmt, success, failure

UNRELEASED_HEADER: Final = "*** Unreleased"


def read_parse_recipe_file(path: Path, methods: dict[Callable] | None) -> Recipes:
    """We want a clean/easy-to-use recipe file, thus, do our own deserialisation."""
    msg = fmt(f"Reading recipes ({path})", color='blue')
    print(msg, flush=True, end="")
    if not path.exists():
        failure()
        print(f"[red]Sorry, unable to find {path} for recipes.")
        sys.exit(1)

    # Read raw..
    raw_recipes = yaml.safe_load(path.read_text())

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

    if methods:
        # Map the built-in methods available onto each recipe step.
        recipes = _add_callables(recipes, methods)

        # Validate that each of the methods are valid.
        if not _validate_recipe_methods(recipes, methods):
            sys.exit(1)

    return recipes


def validate_existing_version_numbers(configuration: Configuration) -> bool:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml"""

    def __get_last_release_from_readme(path_readme: Path = None) -> str:
        """Mini state-machine to find last "release" in our changelog embedded within our README."""
        path_readme = Path.cwd() / "README.org" if path_readme is None else path_readme
        take_next_release = False
        for line in path_readme.read_text().split("\n"):
            if line.startswith(UNRELEASED_HEADER):
                take_next_release = True
                continue
            if take_next_release and line.startswith("*** "):  # eg "*** vX.Y.Z - <aDate>"
                tag = line.split()[1]
                version = tag[1:]
                return version
        return None

    msg = fmt("Checking consistency of versions (pyproject.toml & README.org)", color='blue')
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
    msg = fmt("Validating recipes", color='blue')
    print(msg, flush=True, end="")
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
    for name, recipe in recipes.items():
        for step in recipe:
            if callable_ := step_methods.get(step.method):
                step.callable_ = callable_
    return recipes


def _add_system_recipe_s(recipes: Recipes) -> Recipes:
    """Embellish recipes with our "built-in" one(s)."""
    recipes.set(
        "check",
        Recipe(description="Check configuration only", steps=[Step(method="check"),]))
    recipes.set(
        "show",
        Recipe(description="Show recipe file contents", steps=[Step(method="show"),]))
    return recipes


def gather_available_steps() -> dict[str, Callable]:
    msg = fmt("Reading recipe steps available", color='blue')
    print(msg, flush=True, end="")
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
