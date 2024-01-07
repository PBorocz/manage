"""'Manage' primary entry point."""
import argparse
import sys
from typing import TypeVar

from dotenv import load_dotenv
from rich.console import Console

from manage import PYPROJECT_PATH, __version__
from manage.methods import gather_available_method_classes
from manage.models import Configuration, PyProject, Recipes
from manage.validate import validate_environment, validate_method_classes
from manage.utilities import message, msg_failure, shorten_path

load_dotenv(verbose=True)

TClass = TypeVar("class")

CONSOLE = Console()


def process_arguments() -> [Configuration, PyProject]:
    """Create and run out CLI argument parser with a "raw" read of our pyproject.toml, return it and configuration."""
    # Create our pyproject instance and make sure it's copacetic.
    pyproject = PyProject.factory()
    if not pyproject.validate():
        sys.exit(1)

    # Get (and do some simple validation on) the command-line arguments:
    args: tuple[argparse.Namespace, list[str, str]] = get_args(pyproject)

    # Earliest, simplest exit:
    if args[0].do_version:
        CONSOLE.print(__version__)
        sys.exit(0)

    if args[0].verbose:
        shortened_path = shorten_path(PYPROJECT_PATH, 76)
        message(f"Read {shortened_path}", end_success=True)

    # Given our command-line arguments, create our more structured configuration instance:
    if not (configuration := Configuration.factory(args)):
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

    # "Action" arguments (ie. do something and exit early)
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="do_help",
        default=False,
    )

    parser.add_argument(
        "--print",
        action="store_true",
        dest="do_print",
        default=False,
    )

    parser.add_argument(
        "--version",
        action="store_true",
        dest="do_version",
        default=False,
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        dest="do_validate",
        default=False,
    )

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


def do_help(
    configuration: Configuration,
    pyproject: PyProject,
    method_classes: dict[str, TClass],
    console=CONSOLE,
) -> None:
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
        blue("--version"),
        green("Display current version of this package and exit."),
    )

    table.add_row(
        blue("--print [<recipeName>]"),
        green("Print either all recipes or specified target's recipe and exit."),
    )

    table.add_row(
        blue("--validate"),
        green("Validate your environment and all recipe definitions and exit."),
    )

    table.add_row(
        blue("----------"),
        green("----------"),
    )

    table.add_row(
        blue("--dry_run"),
        green("Run steps in 'dry-run' mode; default is [italic][bold]True[/]."),
    )

    table.add_row(
        blue("--live"),
        green("Run steps in 'live' mode; default is [italic][bold]False[/]."),
    )

    table.add_row(
        blue("--confirm"),
        green(
            "Run steps that have [italic]side-effects[/] with confirmation beforehand; "
            "default is [italic][bold]False[/].",
        ),
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

    panel: Panel = Panel(table, title=green("OPTIONS"), title_align="left")
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
            table.add_row(blue(f"--{name}:{arg.name} [italic]<{arg.name}>[/]"), green(line))

    panel: Panel = Panel(table, title=green("METHOD-BASED COMMAND OPTIONS"), title_align="left")
    console.print(panel)

    ################################################################################
    # Methods available (if verbose)
    ################################################################################
    if configuration.verbose:
        table: Table = Table.grid(expand=True)

        for name, cls_ in method_classes.items():
            table.add_row(
                blue(name),
                green(cls_.__doc__),
            )
        panel: Panel = Panel(table, title=green("METHODS AVAILABLE"), title_align="left")
        console.print(panel)


def validate_target(configuration: Configuration, pyproject: PyProject) -> bool:
    """Make sure the user's requested target is valid.

    By this time, we've already taken care of --help, --version, --print and --validate,
    thus, we *should* have a valid target now to work from.
    """
    # Get list of valid targets from the user's pyproject.toml recipe definitions
    s_targets = pyproject.get_formatted_list_of_targets()

    if not configuration.target:
        msg = (
            f"[red]Sorry, we're expecting a valid recipe target to execute, "
            f"must be one of [yellow][italic]{s_targets}[/].",
        )
        CONSOLE.print(msg)
        return False

    if not pyproject.is_valid_target(configuration.target):
        msg = (
            f"[red]Sorry, [italic]{configuration.target}[/] is not a valid recipe, "
            f"must be one of [yellow][italic]{s_targets}[/]."
        )
        CONSOLE.print(msg)
        return False

    return True


def _go(configuration: Configuration, recipes: Recipes) -> int:
    """Walk the tree twice: first to validate methods for the specified target and then to run if ok."""
    # Validation run..
    if fails := recipes.validate_recipe(configuration, configuration.target):
        for fail in fails:
            msg_failure(f"- {fail}")
        return 1

    # "Real" run..
    try:
        recipes.run(configuration)
    except (KeyboardInterrupt, EOFError):
        ...
    return 0


def main():
    # Before anything else, make sure we're working from the root-level of the target project and have a pyproject.toml.
    if not PYPROJECT_PATH.exists():
        CONSOLE.print(
            "[red]Sorry, you need to run this from the same directory that your pyproject.toml file exists in.",
        )
        sys.exit(1)

    ################################################################################
    # Read our pyproject.toml file and parse (but don't validate) our command-line:
    ################################################################################
    configuration, pyproject = process_arguments()

    ################################################################################
    # Gather available methods from package's library:
    ################################################################################
    if not (method_classes := gather_available_method_classes(configuration.debug)):
        sys.exit(1)

    ################################################################################
    # Do help here AFTER we've setup the configuration object (ie.
    # after incorporating both pyproject.toml defaults and cli args)
    ################################################################################
    if configuration.do_help:
        do_help(configuration, pyproject, method_classes)
        sys.exit(0)

    ################################################################################
    # Convert recipes found in pyproject.toml to strongly-typed instances:
    ################################################################################
    recipes: Recipes = Recipes.factory(configuration, pyproject, method_classes)

    ################################################################################
    # If we're only doing "--print"...do so and WE'RE DONE!
    ################################################################################
    if configuration.do_print:
        recipes.print(configuration)
        sys.exit(0)

    ################################################################################
    # If we're only doing "--validate"...do so and WE'RE DONE!
    ################################################################################
    if configuration.do_validate:
        stat_e = validate_environment(True, configuration, recipes, method_classes)  # Do general validation..
        stat_m = validate_method_classes(configuration, recipes, method_classes)  # Do method validation..
        if stat_e and stat_m:
            sys.exit(0)
        sys.exit(1)

    ################################################################################
    # Validate the user's specific target requested, if nothing valid, WE'RE DONE!
    ################################################################################
    if not validate_target(configuration, pyproject):
        sys.exit(1)

    ################################################################################
    # Do general validation, if bad, WE'RE DONE!
    ################################################################################
    if not validate_environment(False, configuration, recipes, method_classes):
        sys.exit(1)

    ################################################################################
    # Go!
    ################################################################################
    sys.exit(_go(configuration, recipes))
