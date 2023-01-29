"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from manage.dispatch import dispatch
from manage.setup import gather_available_steps, read_parse_recipe_file, validate_existing_version_numbers

from manage.utilities import smart_join, get_package_version_from_pyproject

load_dotenv(verbose=True)

DEFAULT = Path("manage.yaml")


def get_args() -> argparse.Namespace:
    """Define, parse and return command-line args."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "recipe",
        type=str,
        help="Please specify a recipe to run from your recipe file, eg. build, clean, compress etc.",
        default=None
    )

    parser.add_argument(
        "recipe_file",
        type=Path,
        help=f"Override default recipes yaml file, default is '{DEFAULT}'.",
        nargs="?",
        default=DEFAULT,
    )

    args = parser.parse_args()
    if not vars(args) or not args.recipe:
        parser.print_help()
        sys.exit(0)

    return args


def main():
    # Handle arg(s)
    args = get_args()

    # Confirm we're working from the README/root level of our project
    if not (Path.cwd() / "README.org").exists():
        print("[red]Sorry, we need run this from the same direction that your README.org file sits.")
        sys.exit(1)

    # Read configuration and package we're working on
    configuration = get_package_version_from_pyproject()
    if configuration is None:
        sys.exit(1)

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not validate_existing_version_numbers(configuration):
        sys.exit(1)

    # Gather all available steps
    methods = gather_available_steps()
    if not methods:
        sys.exit(1)

    # Read, parse, validate and configure the specified recipe file!
    recipes = read_parse_recipe_file(args.recipe_file, methods)

    # Make sure the user's target request is valid (allowing for "system" recipe(s) built-in)
    if not recipes.check_target(args.recipe.casefold()):
        recipes_console = [f"[italic]{id_}[/]" for id_ in recipes.ids()]
        print(f"Sorry, [red]{args.recipe}[/] is not a valid recipe, must be one of {smart_join(recipes_console)}.")
        sys.exit(1)

    try:
        dispatch(configuration, recipes, args.recipe)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
