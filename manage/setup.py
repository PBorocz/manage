"""Setup functions, not meant for direct calling from recipe file."""
import importlib
import sys
from pathlib import Path
from typing import Callable, Final

import yaml
from rich import print

from manage import methods as methods_module
from manage.models import Configuration, Recipes, Recipe, Step
from manage.utilities import message, success, failure, parse_dynamic_argument


def read_parse_recipes(path_to_recipes: Path) -> [dict, list]:
    """Do the core TOML read of the user's specified Recipes file but don't convert into our object tree."""
    raw_recipes = read_recipes_file(path_to_recipes)  # FIXME: Will sys.exit(1) if file not available!
    return raw_recipes, parse_dynamic_arguments(raw_recipes)


def parse_dynamic_arguments(raw_recipes: dict) -> list[str, type]:
    """Parse optional command-line arguments from the steps in this specific file."""
    # Use a simple, *manual* parse of the recipe file provided!
    arguments = dict()
    errors = list()
    for recipe_name, recipe in raw_recipes.items():
        for step in recipe.get("steps", []):
            for argument, value in step.get("arguments", {}).items():
                name_, type_ = parse_dynamic_argument(argument)
                if name_ in arguments:
                    if type_ != arguments[name_][1]:
                        errors.append(name_)
                else:
                    arguments[name_] = (recipe_name, type_, value)
    if errors:
        print("[red]Sorry, the following arguments in your recipes file have inconsistent types, please correct!")
        for error in errors:
            print(f"[red]{error}")
        sys.exit(1)

    return list(arguments.items())


def read_recipes_file(path_recipes: Path) -> dict:
    """Do a raw read of the specified recipe file path, doing no other processing!."""
    message(f"Reading recipes ({path_recipes})")
    if not path_recipes.exists():
        failure()
        print(f"[red]Sorry, unable to find {path_recipes} for recipes.")
        sys.exit(1)

    # Read raw (safely!)...
    raw_recipes = yaml.safe_load(path_recipes.read_text())
    success()
    return raw_recipes


def uptype_recipes(args, raw_recipes: dict, methods: dict[Callable] | None = None) -> Recipes:
    """We want a clean/easy-to-use recipe file, thus, do our own deserialisation and embellishment."""
    # First, convert to strongly-typed dataclass instances
    d_recipes = dict()
    for id_, raw_recipe in raw_recipes.items():
        recipe = Recipe(**raw_recipe)
        d_recipes[id_] = recipe
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
    """Check that the last released version in README is consistent with canonical version in pyproject.toml."""

    def __get_last_release_from_readme() -> str:
        """Mini state-machine to find last "release" in our changelog embedded within our README."""
        path_readme = Path.cwd() / "README.md"
        header = "###"
        if not path_readme.exists():
            path_readme = Path.cwd() / "README.org"
            header = "***"
            if not path_readme.exists():
                print("[red]Sorry, unable to open EITHER README.md or README.org from the current directory.")
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

    message("Checking consistency of versions (pyproject.toml & README)")
    last_release_version = __get_last_release_from_readme()
    if last_release_version != configuration.version_:
        failure()
        print(f"[red]Warning, pyproject.toml has version: {configuration.version_} "
              f"while last release in README is {last_release_version}!")
        return False
    success()
    return True


def _validate_recipe_methods(recipes: Recipes, step_methods: dict[str, Callable]) -> bool:
    """Make sure all the the methods and steps from our recipes are defined and available."""
    message("Validating recipes")
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
        Recipe(description="Check configuration only.", steps=[Step(method="check", confirm=False)]))
    recipes.set(
        "print",
        Recipe(description="Show/print recipe file contents.", steps=[Step(method="print", confirm=False)]))
    return recipes


# def _override_steps_from_args(recipes: Recipes, args) -> Recipes:
#     """Override any recipe settings with anything from the command-line."""
#     for name, recipe in recipes:
#         for step in recipe:
#             if args.no_confirm is True:  # Careful, default is None otherwise!
#                 # We ARE overriding confirm, is this a case where step.confirm is set?
#                 if step.confirm:
#                     step.confirm = False  # Yes..
#                     message(f"Overriding confirmation: {name} - {step.name()}", color='yellow')
#                     success(color="yellow")
#     return recipes


def gather_available_methods() -> dict[str, Callable]:
    """Read and return all the python-defined step methods available."""

    def __gather_methods_modules():
        """Iterate over all step modules (utility method)."""
        for path in sorted((Path(__file__).parent / Path("methods")).glob("*.py")):
            if path.name.startswith("__"):
                continue

            module = importlib.import_module(f"manage.methods.{path.stem}")

            # Convert methods like "_check_" and "_print" to "check" and "print"
            method_name = path.stem[1:] if path.stem.startswith("_") else path.stem

            yield method_name, getattr(module, "main")

    # Get all the 'main" methods in each python file in the steps module:
    message("Reading recipe steps available")
    methods = {method_name: method for method_name, method in __gather_methods_modules()}
    if not methods:
        failure()
        print("[red]Unable to find any valid command steps in manage/methods/*.py?")
        sys.exit(1)
    success()
    return methods
