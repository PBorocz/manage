"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from manage.dispatch import dispatch
from manage.models import configuration_factory
from manage.setup import (
    gather_available_steps,
    read_parse_recipes,
    uptype_recipes,
    validate_existing_version_numbers,
)

from manage.utilities import smart_join, message, success
load_dotenv(verbose=True)

DEFAULT_RECIPE_PATH = Path("manage.yaml")


def handle_arguments_read_raw_recipes() -> [argparse.Namespace, dict]:
    """Do a two-pass command-line argument parser with a "raw" read of recipes available."""
    #
    # We have a "chicken & egg" problem...ie, can't parse our arguments nicely until we read our recipe file,
    # however, one of the command-line parameters *IS* the recipe file to be read! Thus, this is how we do it:

    # - We read args on a preliminary basis *JUST* to capture the the recipe file to be used (if different from default)
    #   and we use this to do a raw read of the recipe file to get the list of targets defined and arguments possible.
    parser, path_to_recipes = get_recipes_arg()

    # - Then we build on the initial arg-parser on behalf of the rest of the possible arguments on a "official" basis:
    raw_recipes, available_targets, dynamic_arguments = read_parse_recipes(path_to_recipes)

    # Handle the *rest* of the command-line arguments now:
    args = get_all_other_args(parser, available_targets, dynamic_arguments)

    return args, raw_recipes


def get_recipes_arg():
    """Pro-forma arg processing, get the recipe file and find available steps."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-r",
        "--recipes",
        type=Path,
        help=f"Override default recipes yaml file, default is './{DEFAULT_RECIPE_PATH}'.",
        default=DEFAULT_RECIPE_PATH,
    )
    args, _ = parser.parse_known_args()
    return parser, args.recipes


def get_all_other_args(
        initial_parser,
        available_targets: list=[],
        dynamic_arguments: list=[]
) -> None:
    """Build on the initial parser (for just --recipes) and get all other command-line arguments.

    Note: These include both *static* args (like the target) and *dynamic* ones based on our recipe file.
    """
    parser = argparse.ArgumentParser(parents=[initial_parser])

    # Add STATIC command-line arguments (ie. that are always valid)
    s_targets = ": " + smart_join(available_targets) if available_targets else ""
    parser.add_argument(
        "target",
        type=str,
        help=f"Please specify a specific recipe to run from your recipe file{s_targets}",
        default=None,
    )

    parser.add_argument(
        "--confirm",
        help=("Override recipe's 'confirm' setting to run all confirmable "
              "steps as either confirm or don't confirm, default is None."),
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=None,
    )

    # Now, add the *DYNAMIC* arguments to add based on our specific recipe file
    for arg_name, (recipe_name, type_, default) in dynamic_arguments:
        parser.add_argument(
            f"--{arg_name}",
            type=type_,
            help=f"{type_.__name__.title()} argument for recipe '{recipe_name}', default is '{default}'.",
            default=None)

    args = parser.parse_args()

    # We have enough information now to validate the user's specific target requested:
    if args.target.casefold() not in available_targets + ["check", "show"]:
        s_targets = [f"[italic]{id_}[/]" for id_ in available_targets]
        print(f"Sorry, [red]{args.target}[/] is not a valid recipe, must be one of {smart_join(s_targets)}.")
        sys.exit(1)

    return args


def main():

    # Before anything else, confirm we're working from the root-level of the target project
    if not (Path.cwd() / "README.org").exists() and not (Path.cwd() / "README.md").exists():
        print("[red]Sorry, you need to run this from the same directory that your README file exists.")
        sys.exit(1)

    if not (Path.cwd() / "pyproject.toml").exists():
        print("[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists.")
        sys.exit(1)

    # Parse our command-line and do our initial read of the specified recipes file.
    args, raw_recipes = handle_arguments_read_raw_recipes()

    # Read configuration and package we're working on
    configuration = configuration_factory(args)
    if configuration is None:
        sys.exit(1)

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not validate_existing_version_numbers(configuration):
        sys.exit(1)

    # Gather all available steps
    methods = gather_available_steps()
    if not methods:
        sys.exit(1)

    # Calidate and configure the specified recipe file into strongly-typed instances
    recipes = uptype_recipes(args, raw_recipes, methods)

    try:
        dispatch(configuration, recipes, args)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
