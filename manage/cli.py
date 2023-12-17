"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from manage.dispatch import dispatch
from manage.models import configuration_factory, Configuration, PyProject
from manage.setup import (
    gather_available_methods,
    uptype_recipes,
    validate_existing_version_numbers,
)

from manage.utilities import smart_join, get_package_version
load_dotenv(verbose=True)

# FIXME: Assume's we're always running from top-level/project directory!
DEFAULT_PROJECT_PATH = Path.cwd() / "pyproject.toml"
CONSOLE = Console()

def process_arguments() -> [Configuration, PyProject]:
    """Do a two-pass command-line argument parser with a "raw" read of our pyproject.toml."""
    # Read our pyproject.toml file (using verbosity from command-line, not pyproject.toml itself!)
    pyproject = PyProject.factory(DEFAULT_PROJECT_PATH)

    # Get the command-line arguments
    args = get_args(pyproject)

    # Create our configuration instance
    if not (configuration := configuration_factory(args, pyproject)):
        sys.exit(1)

    return configuration, pyproject


def get_args(pyproject: PyProject) -> argparse.Namespace:
    """Build on the initial parser and get the target to run for."""
    parser = argparse.ArgumentParser(add_help=False)

    s_targets = pyproject.get_formatted_list_of_targets()
    parser.add_argument(
        "target",
        type=str,
        action="store",
        nargs="?",
        help=f"Please specify a specific recipe to run from your recipe file: {s_targets}",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False)

    parser.add_argument(
        "--version",
        action="version",
        version=get_package_version(pyproject))

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

    return parser.parse_args()


def do_help(configuration: Configuration, pyproject: PyProject)-> None:
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
    # Recipe targets available..
    ################################################################################
    table = Table.grid(expand=True)
    for name, description in sorted(pyproject.get_target_names_and_descriptions()):
        table.add_row(blue(name), green(description))
    CONSOLE.print(Panel(table, title=green("RECIPES (pyproject.toml)"), title_align="left"))

    ################################################################################
    # Command-line Options
    ################################################################################
    default_dry_run = pyproject.parameters["dry_run"]
    default_live = pyproject.parameters["live"]

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


def main():

    # Before anything else, make sure we're working from the root-level of the target project and have a pyproject.toml.
    if not DEFAULT_PROJECT_PATH.exists():
        CONSOLE.print("[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists.")
        sys.exit(1)

    # Read our pyproject.toml file and parse our command-line
    configuration, pyproject = process_arguments()

    # Do help here AFTER we've setup the configuration object
    # correctly (ie. after incorporating both pyproject.toml defaults
    # and cli args
    if configuration.help:
        do_help(configuration, pyproject)
        sys.exit(0)

    # We have enough information now to validate the user's specific target requested:
    s_targets = pyproject.get_formatted_list_of_targets()
    if not configuration.target:
        msg = f"Sorry, we need a valid recipe target to execute, must be one of {s_targets}."
        CONSOLE.print(msg)
        sys.exit(1)

    if not pyproject.is_valid_target(configuration.target):
        # s_targets = [f"[italic]{id_}[/]" for id_ in available_targets + ["check", "print"]]
        msg = f"Sorry, [red]{configuration.target}[/] is not a valid recipe, must be one of {s_targets}."
        CONSOLE.print(msg)
        sys.exit(1)

    # Gather all available methods from our package's library
    if not (methods := gather_available_methods(configuration.verbose)):
        sys.exit(1)

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not validate_existing_version_numbers(configuration):
        sys.exit(1)

    # Validate and configure the specified recipe file into strongly-typed instances
    recipes = uptype_recipes(configuration, pyproject, methods)

    try:
        dispatch(configuration, recipes)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
