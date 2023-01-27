"""Setup methods, not meant for direct calling from manage.toml."""
import sys
from pathlib import Path
from typing import Callable

from tomli import load
from rich import print

from manage.models import Configuration, Recipes, Recipe, Step
from manage.utilities import fmt, success, failure
from manage import steps as step_module

UNRELEASED_HEADER = "*** Unreleased"
PATH_README = Path.cwd() / "README.org"


def setup() -> tuple[Configuration, dict]:
    """Setup method, return steps/commands, current package name and recipe book."""

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
    recipes = _validate_recipes(recipes, step_methods)
    recipes = _add_system_recipes(recipes, step_methods)

    # FIXME!
    # recipes["__step_callables__"] = step_methods

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
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
    with open(Path("./pyproject.toml"), "rb") as fh_:
        pyproject = load(fh_)

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


def _read_parse_recipe_file() -> Recipes:
    msg = fmt("Reading recipes (manage.toml)", color='blue')
    print(msg, flush=True, end="")
    if not Path("manage.toml").exists():
        failure()
        print("[red]Sorry, unable to find ./manage.toml for recipes.")
        sys.exit(1)

    # Slurp and parse the toml file
    with open("manage.toml", "rb") as stream:
        raw_recipes = load(stream)

    # Deserialise into our types dataclasses:
    recipes = list()
    for id_, raw_recipe in raw_recipes.items():
        recipe = Recipe(id_=id_, **raw_recipe)
        for raw_step in raw_recipe.get("steps", []):
            recipe.steps.append(Step(**raw_step))
        recipes.append(recipe)
    success()
    return Recipes(recipes=recipes)  # Final conversion (no validation)


def _validate_recipes(recipes: Recipes, step_methods: dict[str, Callable]) -> Recipes | None:
    """Make sure all the the methods and steps from our recipes are defined and available"""
    msg = fmt("Validating recipes", color='blue')
    print(msg, flush=True, end="")
    invalid_method_references = list()
    invalid_step_references = list()
    for recipe in recipes:
        for step in recipe:
            if "step" in step:
                step_name = step.get("step")
                if step_name not in recipes:
                    invalid_step_references.append(step_name)
            elif "method" in step:
                method_name = step.get("method")
                if method_name not in step_methods:
                    invalid_method_references.append(method_name)

    if invalid_method_references or invalid_step_references:
        if invalid_method_references:
            print("\n[red]Sorry, error in manage.toml; The following method(s) can't be found:")
            for method_name in invalid_method_references:
                print(f"[red]- {method_name}")
        if invalid_step_references:
            print("\n[red]Sorry, error in manage.toml; The following step(s) can't be found:")
            for step_name in invalid_step_references:
                print(f"[red]- {step_name}")
        failure()
        return None
    success()
    return recipes


def _add_system_recipes(recipes: Recipes, step_methods: dict[str, Callable]) -> Recipes:
    """Embellish recipes with our "built-in" ones and add the corresponding methods"""

    # Add the "callable" method onto each step to be used in dispatching:
    for recipe in recipes:
        for step in recipe:
            if step.method:
                step.callable_ = step_methods.get(step.method)

    # Add our "system"/built-in recipes:
    recipes.recipes.append(
        Recipe(
            id_="check",
            name="Check configuration",
            description="Only executes setup and configuration/validation steps",
            steps=[Step(),]
        )
    )
    return recipes
