"""Utility methods, not meant for direct calling from manage.toml."""
import re
import shlex
import subprocess
import sys
import toml
from importlib import metadata
from pathlib import Path
from typing import Final, Any

from rich import print
from rich.console import Console

TERMINAL_WIDTH: Final = 79


def smart_join(lst: list[str]) -> str:
    """Essentially ', ' but with nicer formatting."""
    return ', '.join(lst[:-1]) + " or " + lst[-1]


def ask_confirm(text: str) -> bool:
    """Ask for confirmation, returns True if "yes" answer or False..Quits if requested!"""
    while True:
        prompt = message(f"{text} (y/N/q)", color="#fffc00")
        answer = Console().input(prompt).lower()
        if answer in ("q"):
            message("Ok", end_success=True)
            sys.exit(0)
        elif answer in ("n", "no", ""):
            return False
        elif answer in ("y", "yes"):
            return True


def success(color: str = "green") -> None:
    """Render/print a success symbol in the specified color."""
    print(f"[{color}]✔")


def failure(color: str = "red") -> None:
    """Render/print a failure symbol (almost always in red but overrideable)."""
    print(f"[{color}]✖")


def replace_rich_markup(string: str) -> str:
    """Return a string without Rich markup."""
    return_ = string
    for pattern in re.findall(r"\[.*?\]", string):
        return_ = return_.replace(pattern, "")
    return return_


def message(message: str, overhead: int = 0, color: str = 'blue', end_success: bool = False, end_failure: bool = False) -> str:
    """Create and print a message string, padded to width (minus markup) and in the specified color."""
    padding = TERMINAL_WIDTH - overhead - len(replace_rich_markup(message))
    formatted = f"[{color}]{message}{'.' * padding}"
    print(formatted, end="", flush=True)
    if end_success:
        success(color=color)
    elif end_failure:
        failure(color=color)


def parse_dynamic_argument(arg: str) -> [str, type]:
    """Parse a dynamic argument name into a typed version.

    Specifically:
    "anArgument"  -> ["anArgument", str]
    "an_argument" -> ["an_argument", str]
    "aStrArg_str" -> ["aStrArg", str]
    "another_int" -> ["another", int]
    "yes_no_bool" -> ["yes_no", bool]
    """
    mapping = {"str": str, "int": int, "bool": bool}
    pieces = arg.split("_")
    if pieces[-1] in mapping:
        type_ = mapping.get(pieces[-1])
        return ["_".join(pieces[0:-1]), type_]
    return [arg, str]


def run(step: Any, command: str) -> tuple[bool, str]:  # FIXME: Should be "Step" but will create circular import!
    """Run the command for the specified Step, capturing output and signal success/failure."""
    if not step.quiet_mode:
        message(f"Running [italic]{command}[/]")

    result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        ################################################
        # Failed:
        ################################################
        # Are we allowed to have error?
        if step and not step.allow_error:
            failure()
            sys.stderr.write(result.stderr.decode())
            return False, result.stderr.decode()

    ################################################
    # Success:
    ################################################
    if not step.quiet_mode:
        success()
        if step.echo_stdout:
            stdout = result.stdout.decode().strip()
            print(f"[grey]{stdout}")

    return True, result.stdout.decode().strip()


def get_package_version_from_pyproject_toml(quiet: bool = False) -> tuple[str | None, str | None]:
    """Read the pyproject.toml file to return *current* package and version we're working with."""
    path_pyproject = Path("./pyproject.toml")

    if not quiet:
        message(f"Reading package & version ({path_pyproject})")

    pyproject = toml.loads(path_pyproject.read_text())

    # Lookup the package which "should" represent the current package we're working on:
    package = None
    if packages := pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
        try:
            # FIXME: For now, we support the first entry in tool.poetry.packages
            #        (even though multiple are allowed)
            package_include = packages[0]
            package = package_include.get("include")
        except IndexError:
            ...

    # Similarly, get our current version:
    version = pyproject.get("tool", {}).get("poetry", {}).get("version", None)
    if package and version:
        if not quiet:
            success()
        return version, package

    if package is None:
        print("[red]Sorry, unable to find a valid 'packages' entry under [tool.poetry] in pyproject.toml!")
    if version is None:
        print("[red]Sorry, unable to find a valid version entry under [tool.poetry] in pyproject.toml")

    if not quiet:
        failure()
    return None, None


def get_version():
    """Return version from installed module or manually from pyproject.toml.

    This is a little subtle. If this is running from an "installed" environment,
    the importlib.metadata *should* work (by getting version from the "build"
    environment used to package the 'manage' projec.

    However, if this is running in a/the development mode (where we're *not*
    "installed" per se), we simply cheat and use the pyproject.toml reader/parser
    we already have but against *out own* pyproject.toml!...too subtle?

    FIXME: Instead of relying upon metadata not working, can we categorically
           know if we're running from a "build" environment??
    """
    try:
        return metadata.version('manage')
    except metadata.PackageNotFoundError:
        version, _ = get_package_version_from_pyproject_toml(quiet=True)
        return version
