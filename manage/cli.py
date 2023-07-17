"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich import print
from rich.console import Console

from manage.dispatch import dispatch
from manage.models import configuration_factory
from manage.setup import (
    gather_available_methods,
    read_parse_recipes,
    uptype_recipes,
    validate_existing_version_numbers,
)

from manage.utilities import smart_join, get_version
load_dotenv(verbose=True)

DEFAULT_RECIPE_PATH = Path("manage.yaml")
CONSOLE = Console()

def handle_arguments_read_raw_recipes() -> [argparse.Namespace, dict]:
    """Do a two-pass command-line argument parser with a "raw" read of recipes available.

    We have a "chicken & egg" problem...ie, can't parse our arguments nicely until we read our
    recipe file, however, one of the command-line parameters *IS* the recipe file to be read!
    """
    # - We read args on a preliminary basis *JUST* to capture the the recipe file to be used (if different from default)
    #   and we use this to do a raw read of the recipe file to get the list of targets defined and arguments possible.
    parser, path_to_recipes = get_recipes_arg()

    # - Then we build on the initial arg-parser on behalf of the rest of the possible arguments on a "official" basis:
    raw_recipes, dynamic_arguments = read_parse_recipes(path_to_recipes)

    # Handle the *rest* of the command-line arguments now:
    args = get_all_other_args(parser, raw_recipes, dynamic_arguments)

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
        recipes: dict,
        dynamic_arguments: list=[],
) -> None:
    """Build on the initial parser (for just --recipes) and get all other command-line arguments.

    Note: These include both *static* args (like the target) and *dynamic* ones based on our recipe file.
    """
    parser = argparse.ArgumentParser("", parents=[initial_parser], add_help=False)

    parser.add_argument(
        "-h",
        "--help",
        action='store_true',
        default=False)

    parser.add_argument(
        '--version',
        action='version',
        version=get_version())

    # Add STATIC command-line arguments (ie. that are always valid)
    available_targets = list(recipes.keys())
    s_targets = ": " + smart_join(available_targets) if available_targets else ""
    parser.add_argument(
        "target",
        type=str,
        action="store",
        nargs="?",
        help=f"Please specify a specific recipe to run from your recipe file{s_targets}",
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

    if args.help:
        do_help(recipes, dynamic_arguments)
        sys.exit(0)

    # We have enough information now to validate the user's specific target requested:
    if args.target.casefold() not in available_targets + ["check", "print"]:
        s_targets = [f"[italic]{id_}[/]" for id_ in available_targets + ["check", "print"]]
        CONSOLE.print(f"Sorry, [red]{args.target}[/] is not a valid recipe, must be one of \\[{smart_join(s_targets)}].")
        sys.exit(1)

    return args

def do_help(recipes: dict, dynamic_arguments: dict):
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.table import Table

    breakpoint()

    def blue(str_: str) -> str:
        return f"[blue]{str_}[/]"

    CONSOLE.print()
    CONSOLE.print("Usage: manage [OPTIONS] <target> [METHOD_ARGS]")
    CONSOLE.print()

    ################################################################################
    table = Table.grid(expand=True)
    # table.add_row("--verbose/-v", "INTEGER Increase verbosity, default is 0 (Info)")
    table.add_row(blue("--version"),    "Show program's version number and exit")
    table.add_row(blue("--help/-h"),    "Show this help message and exit")
    table.add_row(blue("--recipes/-r"), "Override default recipes yaml file, default is './manage.yaml'")
    table.add_row(blue("--no-confirm"),
                  "Override method 'confirm' settings to run [italic]confirmable[/] methods as "\
                  "all confirm or all no confirm, default is 'confirm'")
    CONSOLE.print(Panel(table, title="OPTIONS", title_align="left"))

    ################################################################################
    table = Table.grid(expand=True)
    for recipe_name in sorted(list(recipes.keys())):
        recipe = recipes[recipe_name]
        table.add_row(blue(recipe_name), recipe.get("description"))
    CONSOLE.print(Panel(table, title="TARGETS", title_align="left"))

    ################################################################################
    table = Table.grid(expand=True)
    for arg_name, (recipe_name, type_, default) in dynamic_arguments:
        table.add_row(blue(f"--{arg_name}"), type_.__name__.title(), recipe_name)
    CONSOLE.print(Panel(table, title="METHOD ARGUMENTS", title_align="left"))


def main():

    # Before anything else, make sure we're working from the root-level of the target project
    if not (Path.cwd() / "README.org").exists() and not (Path.cwd() / "README.md").exists():
        CONSOLE.print("[red]Sorry, you need to run this from the same directory that your README file exists.")
        sys.exit(1)

    if not (Path.cwd() / "pyproject.toml").exists():
        CONSOLE.print("[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists.")
        sys.exit(1)

    # Parse our command-line and do our initial read of the specified recipes file.
    args, raw_recipes = handle_arguments_read_raw_recipes()

    # Read configuration and package we're working on
    if not (configuration := configuration_factory(args)):
        sys.exit(1)

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not validate_existing_version_numbers(configuration):
        sys.exit(1)

    # Gather all available steps
    if not (methods := gather_available_methods()):
        sys.exit(1)

    # Validate and configure the specified recipe file into strongly-typed instances
    recipes = uptype_recipes(args, raw_recipes, methods)

    try:
        dispatch(configuration, recipes, args)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
