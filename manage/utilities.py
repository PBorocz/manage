"""Utility methods, not meant for direct calling from manage.toml."""
import shlex
import subprocess
import sys
import toml
from pathlib import Path
from typing import Final

from rich import print
from rich.console import Console

from manage.models import Step, Configuration

TERMINAL_WIDTH: Final = 70


def smart_join(lst: list[str]) -> str:
    """Essentially ', ' but with nicer formatting."""
    return ', '.join(lst[:-1]) + " or " + lst[-1]


def ask_confirm(text: str) -> bool:
    """Ask for confirmation, returns True if "yes" answer, False otherwise."""
    while True:
        prompt = message(f"{text} (y/N)", color="#fffc00")
        answer = Console().input(prompt).lower()
        if answer in ("n", "no", ""):
            return False
        elif answer in ("y", "yes"):
            return True


def success(color: str = "green") -> None:
    """Render/print a success symbol."""
    print(f"[{color}]✔")


def failure() -> None:
    """Render/print a failure symbol."""
    print("[red]✖")


def message(message: str, overhead: int = 0, color: str = 'blue') -> str:
    """Create and print a message string, padding to width and in the specified color."""
    padding = TERMINAL_WIDTH - overhead - len(message)
    formatted = f"[{color}]{message}{'.' * padding}"
    print(formatted, end="", flush=True)


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


def run(step: Step, command: str) -> tuple[bool, str]:
    """Run the command for the specified Step, capturing output and signal success/failure."""
    if not step.quiet_mode:
        message(f"Running [italic]{command}[/italic]", overhead=-17)

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


def configuration_factory(args) -> Configuration | None:
    """Create a Configuration object, setting some attrs from pyproject.toml others from command-line args."""
    version, package = get_package_version_from_pyproject_toml()
    if version is None or package is None:
        return None

    return Configuration(
        version_=version,
        package=package,
        no_confirm=args.no_confirm,
    )


def get_package_version_from_pyproject_toml() -> tuple[str | None, str | None]:
    """Read the pyproject.toml file to return *current* package and version we're working with."""
    path_pyproject = Path("./pyproject.toml")

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
        success()
        return version, package

    if package is None:
        print("[red]Sorry, unable to find a valid 'packages' entry under [tool.poetry] in pyproject.toml!")
    if version is None:
        print("[red]Sorry, unable to find a valid version entry under [tool.poetry] in pyproject.toml")

    failure()
    return None, None
