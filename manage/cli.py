"""'Manage' primary entry point."""
import argparse
import sys
import tomllib
from typing import TypeVar

from dotenv import load_dotenv
from rich.console import Console

from manage import DEFAULT_PROJECT_PATH
from manage.methods import gather_available_method_classes
from manage.models import Configuration, PyProject, Recipes
from manage.validate import validate
from manage.utilities import message, shorten_path

load_dotenv(verbose=True)

TClass = TypeVar("class")

CONSOLE = Console()


def process_arguments() -> [Configuration, PyProject]:
    """Create and run out CLI argument parser with a "raw" read of our pyproject.toml, return it and configuration."""
    # Read our pyproject.toml
    raw_pyproject = tomllib.loads(DEFAULT_PROJECT_PATH.read_text())

    # Create our pyproject instance and make sure it's copacetic.
    pyproject = PyProject.factory(raw_pyproject)
    if not pyproject.validate():
        sys.exit(1)

    # Get (and do some simple validation on) the command-line arguments:
    args: tuple = get_args(pyproject)

    if args[0].verbose:
        shortened_path = shorten_path(DEFAULT_PROJECT_PATH, 76)
        message(f"Read {shortened_path}", end_success=True)

    # Given our command-line arguments, create our more structured configuration instance:
    if not (configuration := Configuration.factory(args, pyproject)):
        sys.exit(1)

    return configuration, pyproject


def get_args(pyproject: PyProject) -> argparse.Namespace:
    """Parse -all- the command-line arguments provide, both known/expected and unknown/step associated."""
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
        "-d",
        "--debug",
        action="store_true",
        default=False,
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
        default=False,
    )

    parser.add_argument(
        "--print",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--confirm",
        help="Override recipe's 'confirm' setting to run all confirmable steps in confirm mode.",
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    # Setup a sub-parser to handle mutually-exclusive setting of --live or --dry-run.
    dry_run_parser = parser.add_mutually_exclusive_group(required=False)

    dry_run_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
    )

    dry_run_parser.add_argument(
        "--live",
        dest="dry_run",
        action="store_false",
    )
    parser.set_defaults(dry_run=True)

    # Parse all the command-line args/parameters provided (both those above and unknown ones)
    args_static, args_dynamic = parser.parse_known_args()

    # Convert to a better data representation
    args_dynamic = _parse_dynamic_args(args_dynamic)

    return args_static, args_dynamic


def _parse_dynamic_args(dynamic_args) -> list[tuple[str, str], str]:
    """Convert/validate the dynamic args to a better data representation."""
    # First, convert from arbitrary inbound list to pairs, ie:
    #   [ "--foo:bar", "baz",   "--method:color", "red"]
    # to:
    #   (["--foo:bar", "baz"], ["--method:color", "red"]):
    paired = [(x, y) for x, y in zip(dynamic_args[::2], dynamic_args[1::2])]

    # Validate that these are all in the right format (ie. as paired method-arg's):
    for method_arg, value in paired:
        if ":" not in method_arg:
            CONSOLE.print(
                "[red]Sorry, unexpected argument or invalid method argument, "
                "must be in the form [italic]<method_name>:<method_argument> <value>[/]",
            )
            CONSOLE.print("[red]For example, [italic]--git_commit:message[/] or [italic]--poetry_version:patch[/]")
            sys.exit(1)

    # Finally, convert from
    #   (["--foo:bar"  , "baz"], ["--method:color"   , "red"])
    # to:
    #   ([(foo", "bar"), "baz"], [("method", "color"), "red"]):
    return_ = []
    for name, value in paired:
        method, arg = name.replace("--", "").split(":")
        return_.append(((method.casefold(), arg.casefold()), value))
    return return_


def do_help(pyproject: PyProject, method_classes: dict[str, TClass], console=CONSOLE) -> None:
    from rich.panel import Panel
    from rich.table import Table

    def green(str_: str) -> str:
        return f"[green]{str_}[/]"

    def blue(str_: str) -> str:
        return f"[blue]{str_}[/]"

    console.print()
    console.print("Usage: manage [OPTIONS] <target> [METHOD_ARGS]")
    console.print()

    ################################################################################
    # Recipe targets available..
    ################################################################################
    table = Table.grid(expand=True)
    for name, description in sorted(pyproject.get_target_names_and_descriptions()):
        table.add_row(blue(name), green(f"{description}."))
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
        blue("--print"),
        green("Print either all recipes or specified target's recipe and exit."),
    )

    table.add_row(
        blue("--verbose/-v"),
        green(
            "Run steps in verbose mode [italic](including method stdout if available)[/]; "
            "default is [italic][bold]False[/].",
        ),
    )

    table.add_row(
        blue("--debug/-d"),
        green(
            "Run in debug mode; default is [italic]False[/].",
        ),
    )

    table.add_row(
        blue("--confirm"),
        green(
            "Override all method-based 'confirm' settings to run [italic]confirmable[/] methods as "
            "all [bold]confirm[/]; "
            "default is [italic][bold]False[/].",
        ),
    )

    table.add_row(
        blue("--dry_run"),
        green("Run steps in 'dry-run' mode; default is [italic][bold]True[/]."),
    )

    table.add_row(
        blue("--live"),
        green("Run steps in 'live' mode; default is [italic][bold]False[/]."),
    )

    panel: Panel = Panel(table, title=green("BUILT-IN COMMAND OPTIONS"), title_align="left")
    console.print(panel)

    ################################################################################
    # Methods available
    ################################################################################
    table: Table = Table.grid(expand=True)

    for name, cls_ in method_classes.items():
        table.add_row(
            blue(name),
            green(cls_.__doc__),
        )
    panel: Panel = Panel(table, title=green("CONFIGURATION METHODS AVAILABLE"), title_align="left")
    console.print(panel)

    ################################################################################
    # Method-based command-line arguments available
    ################################################################################
    table: Table = Table.grid(expand=True)

    for name, cls_ in method_classes.items():
        for arg in getattr(cls_, "args", []):
            line = ""
            if arg.default:
                line = f"Default is [italic][bold]{arg.default}[/]"
            table.add_row(blue(f"--{name}:{arg.name}"), green(line))

    panel: Panel = Panel(table, title=green("METHOD-BASED COMMAND OPTIONS"), title_align="left")
    console.print(panel)


def main():
    # Before anything else, make sure we're working from the root-level of the target project and have a pyproject.toml.
    if not DEFAULT_PROJECT_PATH.exists():
        CONSOLE.print(
            "[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists in.",
        )
        sys.exit(1)

    ################################################################################
    # Read our pyproject.toml file and parse (but don't validate) our command-line:
    ################################################################################
    configuration, pyproject = process_arguments()
    s_targets = pyproject.get_formatted_list_of_targets()

    ################################################################################
    # Gather available methods from package's library:
    ################################################################################
    if not (method_classes := gather_available_method_classes(configuration.debug)):
        sys.exit(1)

    ################################################################################
    # Do help here AFTER we've setup the configuration object (ie.
    # after incorporating both pyproject.toml defaults and cli args)
    ################################################################################
    if configuration.help:
        do_help(pyproject, method_classes)
        sys.exit(0)

    ################################################################################
    # Convert recipes found in pyproject.toml to strongly-typed instances:
    ################################################################################
    recipes: Recipes = Recipes.factory(configuration, pyproject, method_classes)

    ################################################################################
    # Validate the user's specific target requested:
    ################################################################################
    if configuration.target:
        if not pyproject.is_valid_target(configuration.target):
            msg = (
                f"[red]Sorry, [italic]{configuration.target}[/] is not a valid recipe, "
                f"must be one of [yellow][italic]{s_targets}[/]."
            )
            CONSOLE.print(msg)
            sys.exit(1)
    elif not configuration.print:
        msg = f"Sorry, we need a valid recipe target to execute, must be one of [yellow]{s_targets}[/]."
        CONSOLE.print(msg)
        sys.exit(1)

    ################################################################################
    # If we're only doing, print...do so and WE'RE DONE!
    ################################################################################
    if configuration.print:
        recipes.print(configuration)
        sys.exit(0)

    ################################################################################
    # Do some validation:
    ################################################################################
    if not validate(configuration, recipes, method_classes):
        sys.exit(1)

    ################################################################################
    # Walk the tree twice, first to validate method instances and then to run.
    ################################################################################
    try:
        recipes.walk(configuration, True)
        recipes.walk(configuration, False)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
