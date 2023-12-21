"""'Manage' primary entry point."""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from manage.dispatch import dispatch
from manage.methods import gather_available_method_classes
from manage.models import Configuration, PyProject, Recipes
from manage.validate import validate
from manage.utilities import message, shorten_path

load_dotenv(verbose=True)

# FIXME: Assume's we're always running from top-level/project directory!
DEFAULT_PROJECT_PATH = Path.cwd() / "pyproject.toml"
CONSOLE = Console()


def process_arguments() -> [Configuration, PyProject]:
    """Create and run out CLI argument parser with a "raw" read of our pyproject.toml, return it and configuration."""
    # Read our pyproject.toml
    pyproject = PyProject.factory(DEFAULT_PROJECT_PATH)

    # Get (and do some simple validation on) the command-line arguments:
    args = get_args(pyproject)

    if args.verbose:
        shortened_path = shorten_path(DEFAULT_PROJECT_PATH, 76)
        message(f"Read {shortened_path}", end_success=True)

    # Given our command-line arguments, now we can create our configuration instance:
    if not (configuration := Configuration.factory(args, pyproject)):
        sys.exit(1)

    return configuration, pyproject


def get_args(pyproject: PyProject) -> argparse.Namespace:
    """Build on the initial parser and get the target to run for."""
    parser = argparse.ArgumentParser(add_help=False)

    s_targets: str = pyproject.get_formatted_list_of_targets()
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
        default=pyproject.get_parm("default_verbose"),
    )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--confirm",
        help="Override recipe's 'confirm' setting to run all confirmable steps in confirm mode.",
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=pyproject.get_parm("default_confirm"),
    )

    parser.add_argument(
        "--live",
        action="store_true",
        default=pyproject.get_parm("default_live"),
    )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        default=pyproject.get_parm("default_dry_run"),
    )

    return parser.parse_args()


def do_help(pyproject: PyProject, console=CONSOLE) -> None:
    from rich.panel import Panel
    from rich.table import Table

    def green(str_: str) -> str:
        return f"[green]{str_}[/]"

    def blue(str_: str) -> str:
        return f"[blue]{str_}[/]"

    console.print()
    console.print("Usage: manage [OPTIONS] <target>")
    # console.print("Usage: manage [OPTIONS] <target> [METHOD_ARGS]")
    console.print()

    ################################################################################
    # Recipe targets available..
    ################################################################################
    table = Table.grid(expand=True)
    for name, description in sorted(pyproject.get_target_names_and_descriptions()):
        table.add_row(blue(name), green(description))
    panel: Panel = Panel(table, title=green("RECIPES (pyproject.toml)"), title_align="left")
    console.print(panel)

    ################################################################################
    # Command-line Options
    ################################################################################
    table: Table = Table.grid(expand=True)

    table.add_row(
        blue("--help/-h"),
        green("Show this help message and exit."),
    )

    table.add_row(
        blue("--verbose/-v"),
        green(
            "Run steps in verbose mode [italic](including method stdout if available)[/]; "
            f'default is [italic][bold]{pyproject.get_parm("default_verbose")}[/].',
        ),
    )
    table.add_row(
        blue("--confirm"),
        green(
            "Override all method-based 'confirm' settings to run [italic]confirmable[/] methods as "
            "all [bold]confirm[/]; "
            f'default is [italic][bold]{pyproject.get_parm("default_confirm")}[/].',
        ),
    )

    table.add_row(
        blue("--dry_run"),
        green(
            "Run steps in 'dry-run' mode; " f'default is [italic][bold]{pyproject.get_parm("default_dry_run")}[/].',
        ),
    )

    table.add_row(
        blue("--live"),
        green(
            "Run steps in 'live' mode; " f'default is [italic][bold]{pyproject.get_parm("default_live")}[/].',
        ),
    )

    panel: Panel = Panel(table, title=green("OPTIONS"), title_align="left")
    console.print(panel)


def main():
    # Before anything else, make sure we're working from the root-level of the target project and have a pyproject.toml.
    if not DEFAULT_PROJECT_PATH.exists():
        CONSOLE.print(
            "[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists in.",
        )
        sys.exit(1)

    ################################################################################
    # Read our pyproject.toml file and parse our command-line
    ################################################################################
    configuration, pyproject = process_arguments()

    s_targets = pyproject.get_formatted_list_of_targets()

    ################################################################################
    # Gather all available methods from our package's library (doesn't rely on anything else besides verbosity)
    ################################################################################
    if not (method_classes := gather_available_method_classes(configuration.verbose)):
        sys.exit(1)

    ################################################################################
    # Do help here AFTER we've setup the configuration object (ie.
    # after incorporating both pyproject.toml defaults and cli args)
    ################################################################################
    if configuration.help:
        do_help(pyproject)
        sys.exit(0)

    ################################################################################
    # We have enough information now to validate the user's specific target requested:
    ################################################################################
    if not configuration.target:
        msg = f"Sorry, we need a valid recipe target to execute, must be one of [yellow]{s_targets}[/]."
        CONSOLE.print(msg)
        sys.exit(1)

    if not pyproject.is_valid_target(configuration.target):
        msg = (
            f"Sorry, [red]{configuration.target}[/] is not a valid recipe, "
            f"must be one of [yellow][italic]{s_targets}[/]."
        )
        CONSOLE.print(msg)
        sys.exit(1)

    ################################################################################
    # Convert specified recipe file raw data into strongly-typed instances.
    ################################################################################
    recipes: Recipes = Recipes.factory(configuration, pyproject)

    ################################################################################
    # Do a full validation suite.
    ################################################################################
    if not validate(configuration, recipes, method_classes):
        sys.exit(1)

    ################################################################################
    # Laminate all the method/class operations onto our recipes.
    ################################################################################
    recipes.laminate_method_classes(configuration, method_classes)

    ################################################################################
    # Dispatch to our target and run!
    ################################################################################
    try:
        dispatch(configuration, recipes)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
