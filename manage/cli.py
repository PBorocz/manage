"""'Manage' primary entry point."""
import sys
import argparse

from dotenv import load_dotenv
from rich import print

from manage.dispatch import dispatch
from manage.setup import setup
from manage.utilities import smart_join

load_dotenv(verbose=True)


def main():
    # Run our own setup steps, reading/validating the recipe file and getting some core environment information etc. If there are
    # any issues, setup will sys.exit(1) after providing feedback as to what's wrong.
    configuration, recipes = setup()
    recipes_raw = sorted([key for key in recipes.keys() if not key.startswith("__")])
    recipes_console = [f"[italic]{key}[/]" for key in recipes_raw]

    # Handle arg(s)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "recipe",
        type=str,
        help=f"Please specify a recipe to run, available now are: {smart_join(recipes_raw)}",
        nargs="?",
        default=None
    )
    args = parser.parse_args()
    if not vars(args) or not args.recipe:
        parser.print_help()
        sys.exit(0)

    # Validate requested recipe (allowing for "system" recipe(s) built-in)
    if args.recipe.casefold() not in recipes:
        print(f"Sorry, [red]{args.recipe}[/] is not a valid recipe, must be one of {smart_join(recipes_console)}.")
        sys.exit(1)

    try:
        dispatch(configuration, recipes, args.recipe)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
