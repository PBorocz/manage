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
    read_pyproject,
    uptype_recipes,
    validate_existing_version_numbers,
)

from manage.utilities import smart_join, get_package_version
load_dotenv(verbose=True)

# FIXME: Assume's we're always running from top-level/project directory!
DEFAULT_PROJECT_PATH = Path.cwd() / "pyproject.toml"
CONSOLE = Console()

def process_arguments() -> [argparse.Namespace, dict, dict]:
    """Do a two-pass command-line argument parser with a "raw" read of recipes available.

    We have a "chicken & egg" problem...ie, can't parse our arguments nicely until we read our
    pyproject file.
    """
    # We read args on a preliminary basis *JUST* to capture the the
    # recipe file to be used (if different from default); we use this
    # to do a raw read of the recipe file to get the list of targets
    # defined and arguments possible.
    parser, args_verbose = get_args_pass_1()

    # Then we build on the initial arg-parser to include the list of all recipes available.
    raw_pyproject = read_pyproject(args_verbose, DEFAULT_PROJECT_PATH)

    args, parameters, available_targets = get_args_pass_2(parser, raw_pyproject)

    return args, parameters, raw_pyproject


def get_args_pass_1():
    """Pro-forma arg processing, get an alternate recipe file and non-recipe-file based arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False)
    args, _ = parser.parse_known_args()
    return parser, args.verbose


def get_args_pass_2(initial_parser, raw_pyproject: dict) -> [argparse.Namespace, dict, list[str]]:
    """Build on the initial parser and get the target to run for."""
    parser = argparse.ArgumentParser("", parents=[initial_parser], add_help=False)

    # Get our configuration from the raw pyproject dictionary:
    parameters = dict()
    for name, obj in raw_pyproject.get("tool", {}).get("manage", {}).items():
        if name == "recipes":
            recipes = obj
        else:
            parameters[name] = obj

    names_and_descriptions = [(name, definition.get("description", "")) for name, definition in recipes.items()]
    available_targets = [recipe_name for (recipe_name, description) in names_and_descriptions]
    s_targets = ": " + smart_join(available_targets) if available_targets else ""

    # Add the rest of the command-line arguments:
    parser.add_argument(
        "target",
        type=str,
        action="store",
        nargs="?",
        help=f"Please specify a specific recipe to run from your recipe file: {s_targets}",
    )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False)

    parser.add_argument(
        "--version",
        action="version",
        version=get_package_version(raw_pyproject))

    parser.add_argument(
        "--confirm",
        help=("Override recipe's 'confirm' setting to run all confirmable "
              "steps as either confirm or don't confirm, default is None."),
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=None,
    )

    parser.add_argument(
        "--live",
        action="store_true",
        default=False)

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False)

    args = parser.parse_args()

    # # If we're doing help, use our own method and we're done!
    # if args.help:
    #     do_help(parameters, names_and_descriptions)
    #     sys.exit(0)

    # # We have enough information now to validate the user's specific target requested:
    # if not args.target or args.target.casefold() not in available_targets + ["check", "print"]:
    #     s_targets = [f"[italic]{id_}[/]" for id_ in available_targets + ["check", "print"]]
    #     msg = f"Sorry, [red]{args.target}[/] is not a valid recipe, must be one of \\[{smart_join(s_targets)}]."
    #     CONSOLE.print(msg)
    #     sys.exit(1)

    return args, parameters, available_targets


def do_help(parameters: dict, names_and_descriptions: list[str])-> None:
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

    default_dry_run = parameters.get("dry_run", True) # By default if NOTHING else
    default_live = parameters.get("live", False)      # is specified, stay safe.

    ################################################################################
    table = Table.grid(expand=True)
    table.add_row(blue("--version"),
                  green("Show program's version number and exit."))

    table.add_row(blue("--help/-h"),
                  green("Show this help message and exit."))

    table.add_row(blue("--verbose/-v"),
                  green("Run steps in verbose mode [italic](including method stdout if available)[/]."))

    table.add_row(blue("--dry-run"),
                  green(f"Run steps in 'dry-run' mode, default is {default_dry_run}."))

    table.add_row(blue("--live"),
                  green(f"Run steps in 'live' mode, default is {default_live}."))

    table.add_row(blue("--confirm"),
                  green("Override all method-based 'confirm' settings to run [italic]confirmable[/] methods as "\
                  "all [bold]confirm[/]."))

    table.add_row(blue("--no-confirm"),
                  green("Override all method-based 'confirm' settings to run [italic]confirmable[/] methods as "\
                  "all [bold]no[/] confirm."))

    CONSOLE.print(Panel(table, title=green("OPTIONS"), title_align="left"))

    ################################################################################
    table = Table.grid(expand=True)
    for name, description in sorted(names_and_descriptions):
        table.add_row(blue(name), green(description))
    CONSOLE.print(Panel(table, title=green("TARGETS (pyproject.toml)"), title_align="left"))


def main():

    # Before anything else, make sure we're working from the root-level of the target project and have a pyproject.toml.
    if not DEFAULT_PROJECT_PATH.exists():
        CONSOLE.print("[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists.")
        sys.exit(1)

    # Parse our command-line and do our initial read of the specified pyproject file.
    args, parameters, raw_pyproject = process_arguments()

    # Read configuration and package we're working on
    if not (configuration := configuration_factory(args, parameters, raw_pyproject)):
        sys.exit(1)

    # START HERE!!!
    # Do help here AFTER we've setup the configuration object correctly..
    # if args.help:
    #     do_help(parameters, names_and_descriptions)
    #     sys.exit(0)

    # # We have enough information now to validate the user's specific target requested:
    # if not args.target or args.target.casefold() not in available_targets + ["check", "print"]:
    #     s_targets = [f"[italic]{id_}[/]" for id_ in available_targets + ["check", "print"]]
    #     msg = f"Sorry, [red]{args.target}[/] is not a valid recipe, must be one of \\[{smart_join(s_targets)}]."
    #     CONSOLE.print(msg)
    #     sys.exit(1)

    # Gather all available methods from our package's library
    if not (methods := gather_available_methods(configuration.verbose)):
        sys.exit(1)

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not validate_existing_version_numbers(configuration):
        sys.exit(1)

    # Validate and configure the specified recipe file into strongly-typed instances
    recipes = uptype_recipes(configuration, raw_pyproject, methods)

    try:
        dispatch(configuration, recipes)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
