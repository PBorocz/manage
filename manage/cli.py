"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from manage.dispatch import dispatch
from manage.models import configuration_factory
from manage.setup import (
    gather_available_methods,
    read_recipe_file,
    uptype_recipes,
    validate_existing_version_numbers,
)

from manage.utilities import smart_join, get_package_version
load_dotenv(verbose=True)

DEFAULT_RECIPE_PATH = Path("./manage.yaml")
CONSOLE = Console()

def process_arguments() -> [argparse.Namespace, dict]:
    """Do a two-pass command-line argument parser with a "raw" read of recipes available.

    We have a "chicken & egg" problem...ie, can't parse our arguments nicely until we read our
    recipe file, however, one of the command-line parameters *IS* the recipe file to be read!
    """
    # We read args on a preliminary basis *JUST* to capture the the recipe file to be used (if different from default)
    # nd we use this to do a raw read of the recipe file to get the list of targets defined and arguments possible.
    parser, path_recipes, arg_verbose = get_args_pass_1()

    # Then we build on the initial arg-parser to include the list of all recipes available.
    raw_recipes = read_recipe_file(arg_verbose, path_recipes)
    args = get_args_pass_2(parser, path_recipes, raw_recipes)

    return args, raw_recipes


def get_args_pass_1():
    """Pro-forma arg processing, get the recipe file and non-recipe-file based arguments."""
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        "-r",
        "--recipes",
        type=Path,
        help=f"Override default recipes yaml file, default is './{DEFAULT_RECIPE_PATH}'.",
        default=DEFAULT_RECIPE_PATH,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False)

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False)

    parser.add_argument(
        "--version",
        action="version",
        version=get_package_version())

    parser.add_argument(
        "--confirm",
        help=("Override recipe's 'confirm' setting to run all confirmable "
              "steps as either confirm or don't confirm, default is None."),
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=None,
    )

    args, _ = parser.parse_known_args()
    return parser, args.recipes, args.verbose


def get_args_pass_2(
        initial_parser,
        path_recipes: Path,
        raw_recipes: dict,
) -> None:
    """Build on the initial parser and get the target to run for."""
    parser = argparse.ArgumentParser("", parents=[initial_parser], add_help=False)

    # Add command-line argument for target to execute (since it depends on the recipe file.
    available_targets = list(raw_recipes.keys())
    s_targets = ": " + smart_join(available_targets) if available_targets else ""
    parser.add_argument(
        "target",
        type=str,
        action="store",
        nargs="?",
        help=f"Please specify a specific recipe to run from your recipe file{s_targets}",
    )

    args = parser.parse_args()

    # If we're doing help, use our own method and we're done!
    if args.help:
        do_help(path_recipes, raw_recipes)
        sys.exit(0)

    # We have enough information now to validate the user's specific target requested:
    if not args.target or args.target.casefold() not in available_targets + ["check", "print"]:
        s_targets = [f"[italic]{id_}[/]" for id_ in available_targets + ["check", "print"]]
        msg = f"Sorry, [red]{args.target}[/] is not a valid recipe, must be one of \\[{smart_join(s_targets)}]."
        CONSOLE.print(msg)
        sys.exit(1)

    return args


def do_help(path_recipes: Path, raw_recipes: dict):
    from rich.panel import Panel
    from rich.table import Table

    def green(str_: str) -> str:
        return f"[green]{str_}[/]"

    def blue(str_: str) -> str:
        return f"[blue]{str_}[/]"

    CONSOLE.print()
    CONSOLE.print("Usage: manage [OPTIONS] <target>")
    # CONSOLE.print("Usage: manage [OPTIONS] <target> [METHOD_ARGS]")
    CONSOLE.print()

    ################################################################################
    table = Table.grid(expand=True)
    table.add_row(blue("--version"),    green("Show program's version number and exit."))
    table.add_row(blue("--help/-h"),    green("Show this help message and exit."))
    table.add_row(blue("--verbose/-v"), green("Run steps in verbose mode [italic](including method stdout if available)[/]."))
    table.add_row(blue("--recipes/-r"), green("Override default recipes yaml file, default is [bold]./manage.yaml[/]."))
    table.add_row(blue("--confirm"),
                  green("Override all method-based 'confirm' settings to run [italic]confirmable[/] methods as "\
                  "all [bold]confirm[/]."))
    table.add_row(blue("--no-confirm"),
                  green("Override all method-based 'confirm' settings to run [italic]confirmable[/] methods as "\
                  "all [bold]no[/] confirm."))
    CONSOLE.print(Panel(table, title=green("OPTIONS"), title_align="left"))

    ################################################################################
    table = Table.grid(expand=True)
    for recipe_name in sorted(list(raw_recipes.keys())):
        recipe = raw_recipes[recipe_name]
        table.add_row(blue(recipe_name), green(recipe.get("description")))
    CONSOLE.print(Panel(table, title=green(f"TARGETS ({path_recipes})"), title_align="left"))


def main():

    # Before anything else, make sure we're working from the root-level of the target project
    if not (Path.cwd() / "pyproject.toml").exists():
        CONSOLE.print("[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists.")
        sys.exit(1)

    # Parse our command-line and do our initial read of the specified recipes file.
    args, raw_recipes = process_arguments()

    # Read configuration and package we're working on
    if not (configuration := configuration_factory(args)):
        sys.exit(1)

    # Gather all available methods from our package's library
    if not (methods := gather_available_methods(configuration.verbose)):
        sys.exit(1)

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not validate_existing_version_numbers(configuration):
        sys.exit(1)

    # Validate and configure the specified recipe file into strongly-typed instances
    recipes = uptype_recipes(configuration, raw_recipes, methods)

    try:
        dispatch(configuration, recipes)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
