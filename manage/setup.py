"""Setup functions, not meant for direct calling from manage.toml."""
import sys
import toml
from pathlib import Path
from typing import Callable

from rich import print

from manage.models import Configuration, Recipes, Recipe, Step
from manage.utilities import fmt, success, failure
from manage import steps as step_module

UNRELEASED_HEADER = "*** Unreleased"
PATH_README = Path.cwd() / "README.org"


def setup() -> tuple[Configuration, Recipes]:
    """Driver 'setup' method, returns configuration and user recipes."""

    # Confirm we're working from the README/root level of our project
    if not (Path.cwd() / "README.org").exists():
        print("[red]Sorry, we need run this from the same direction that your README.org file sits.")
        sys.exit(1)

    # Gather all available steps
    step_methods = _gather_available_steps()
    if not step_methods:
        sys.exit(1)

    # Read configuration and package we're working on
    configuration = _get_package_version_from_pyproject()
    if configuration is None:
        sys.exit(1)

    # Read the recipes from specified manage.toml file
    recipes = _read_parse_recipe_file()

    # Map the built-in methods available onto each recipe step.
    recipes = _add_callables(recipes, step_methods)

    # Validate that each of the methods are valid.
    recipes = _validate_recipe_methods(recipes, step_methods)

    # Add system recipe target(s)
    recipes = _add_system_recipe_s(recipes)

    # Finally, validate that version numbers are consistent between pyproject.toml and README's change history.
    if not _validate_existing_version_numbers(configuration):
        sys.exit(1)

    return configuration, recipes


def __get_last_release_from_readme() -> str:
    """Mini state-machine to find last "release" in our changelog embedded within our README."""
    take_next_release = False
    for line in PATH_README.read_text().split("\n"):
        if line.startswith(UNRELEASED_HEADER):
            take_next_release = True
            continue
        if take_next_release and line.startswith("*** "):  # eg "*** vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            return version
    return None


def _validate_existing_version_numbers(configuration: Configuration) -> bool:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml"""
    msg = fmt("Checking consistency of versions (pyproject.toml & README.org)", color='blue')
    print(msg, end="", flush=True)
    last_release_version = __get_last_release_from_readme()
    if last_release_version != configuration.version_:
        failure()
        print(f"[red]Warning, pyproject.toml has version: {configuration.version_} while last release in README is {last_release_version}!")
        return False
    success()
    return True


def _get_package_version_from_pyproject() -> Configuration:
    """Read the pyproject.toml file to return current package and version we're working with."""
    msg = fmt("Reading package & version (pyproject.toml)", color='blue')
    print(msg, end="", flush=True)
    pyproject = toml.loads(Path("./pyproject.toml").read_text())

    # Lookup the package which "should" represent the current package we're working on:
    package = None
    if packages := pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
        try:
            # FIXME: For now, we support the first entry in tool.poetry.packages
            #        (even though multiple are allowed)
            package_include = packages[0]
            package = package_include.get("include")
        except IndexError:
            ...

    # Similarly, get our current version:
    version = pyproject.get("tool", {}).get("poetry", {}).get("version", None)
    if package and version:
        success()
        return Configuration(version_=version, package=package)

    if package is None:
        print("[red]Sorry, unable to find a valid 'packages' entry under [tool.poetry] in pyproject.toml!")
    if version is None:
        print("[red]Sorry, unable to find a valid version entry under [tool.poetry] in pyproject.toml")

    failure()
    return None


def _gather_available_steps() -> dict[str, Callable]:
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


def _read_parse_recipe_file(path: Path = Path("manage.toml")) -> Recipes:
    """We want a clean/easy-to-use recipe file, thus, do our own deserialisation."""
    msg = fmt(f"Reading recipes ({path})", color='blue')
    print(msg, flush=True, end="")
    if not path.exists():
        failure()
        print(f"[red]Sorry, unable to find {path} for recipes.")
        sys.exit(1)

    # Read raw..
    raw_recipes = toml.loads(path.read_text()).get("recipes")

    # ..and deserialise into our types dataclasses:
    recipes = dict()
    for raw_recipe in raw_recipes:
        recipe = Recipe(**raw_recipe)
        recipes[recipe.name] = recipe
    success()
    return Recipes.parse_obj(recipes)  # Final conversion (no validation)


def _validate_recipe_methods(recipes: Recipes, step_methods: dict[str, Callable]) -> Recipes | None:
    """Make sure all the the methods and steps from our recipes are defined and available"""
    msg = fmt("Validating recipes", color='blue')
    print(msg, flush=True, end="")
    if invalid_actions := recipes.validate_step_actions(step_methods):
        print("\n[red]Sorry, error in manage.toml; The following action(s) can't be found:")
        for action in invalid_actions:
            print(f"[red]- {action}")
        failure()
        return None
    success()
    return recipes


def _add_callables(recipes: Recipes, step_methods: dict[str, Callable]) -> Recipes:
    """Add the "callable" method onto each step to be used in dispatching."""
    for name, recipe in recipes.items():
        for step in recipe:
            if callable_ := step_methods.get(step.action):
                step.callable_ = callable_
    return recipes


def _add_system_recipe_s(recipes: Recipes) -> Recipes:
    """Embellish recipes with our "built-in" one(s)."""
    recipes.set(
        "check",
        Recipe(
            name="Check configuration",
            description="Only executes setup and configuration/validation steps",
            steps=[Step(action="__check__"),]
        ))
    return recipes
