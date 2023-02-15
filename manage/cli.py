"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from manage.dispatch import dispatch
from manage.setup import (
    gather_available_steps,
    read_recipe_file,
    parse_recipe_file,
    validate_existing_version_numbers,
)

from manage.utilities import smart_join, ConfigurationFactory, SimpleObj

load_dotenv(verbose=True)

DEFAULT_RECIPE_PATH = Path("manage.yaml")


def get_args(
        pro_forma_parser,
        available_targets: list=[],
        dynamic_arguments: list=[]
) -> None:

    parser = argparse.ArgumentParser(parents=[pro_forma_parser])

    # Add other a priori command-line arguments:
    s_targets = ": " + ', '.join(available_targets) if available_targets else ""
    parser.add_argument(
        "target",
        type=str,
        help=f"Please specify a specific recipe to run from your recipe file{s_targets}",
        default=None
    )

    parser.add_argument(
        "--no-confirm",
        help=f"Override confirm=True recipes settings and run in NO confirmation mode, default is False.",
        action='store_true'
    )

    # Do we have any dynamic arguments to add based on our specific recipe file?
    for dynamic_argument in dynamic_arguments:
        parser.add_argument(
            f"--{dynamic_argument}",
            type=str,
            nargs=1,
            default=None)

    return parser.parse_args()


def get_arg_preliminary():
    """Pro-forma Arg processing, get the recipe file and find available steps."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-r",
        "--recipes",
        type=Path,
        help=f"Override default recipes yaml file, default is './{DEFAULT_RECIPE_PATH}'.",
        default=DEFAULT_RECIPE_PATH,
    )
    args, _ = parser.parse_known_args()
    return parser, args


def get_preliminary_recipes(args):
    raw_recipes = read_recipe_file(args.recipes)

    # Capture: list of available recipe targets appropriate.
    available_targets = list(raw_recipes.keys())
    dynamic_arguments = set()

    # Capture: list of optional command-line arguments from the steps in this specific file:
    # (simple, manual parse of the recipe file provided)
    for recipe in raw_recipes.values():
        for step in recipe.get("steps", []):
            for argument in step.get("arguments", []):
                dynamic_arguments.add(argument)

    return raw_recipes, available_targets, list(dynamic_arguments)


def main():
    # Before anything else, confirm we're working from the root-level of the target project
    if not (Path.cwd() / "README.org").exists() and not (Path.cwd() / "README.md").exists():
        print("[red]Sorry, you need to run this from the same directory that your README file exists.")
        sys.exit(1)

    if not (Path.cwd() / "pyproject.toml").exists():
        print("[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists.")
        sys.exit(1)

    # Resolve the "chicken & egg" problem...ie, can't parse our arguments nicely until
    # we read our recipe file, however, one of the command-line parameters *IS* the recipe
    # file to be read!

    # Thus, we process/parse args *twice*, once on a pro-forma/preliminary basis to capture the
    # minimal amount of information necessary to properly read args and read recipe file and then
    # again on a "official" basis.
    preliminary_parser, preliminary_args = get_arg_preliminary()

    raw_recipes, available_targets, dynamic_arguments = get_preliminary_recipes(preliminary_args)

    # Handle the *rest* of the command-line arguments now:
    args = get_args(preliminary_parser, available_targets, dynamic_arguments)

    # We have enough information now to validate the user's specific target requested:
    if args.target.casefold() not in available_targets:
        s_targets = [f"[italic]{id_}[/]" for id_ in available_targets]
        print(f"Sorry, [red]{args.target}[/] is not a valid recipe, must be one of {smart_join(s_targets)}.")
        sys.exit(1)

    # Read configuration and package we're working on
    configuration = ConfigurationFactory(args)
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
    recipes = parse_recipe_file(args, raw_recipes, methods)

    try:
        dispatch(configuration, recipes, args)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
