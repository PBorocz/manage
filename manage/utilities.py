"""Utility methods, not meant for direct calling from manage.toml."""
import re
import shlex
import subprocess
import sys
from typing import Final, TypeVar

from rich import print
from rich.console import Console


TERMINAL_WIDTH: Final = 79

TStep = TypeVar("Step")


def smart_join(lst: list[str], with_or: bool = False, delim: str = ",") -> str:
    """Essentially ', ' but with nicer formatting."""
    s_delim = f"{delim} "
    if with_or:
        return s_delim.join(lst[:-1]) + " or " + lst[-1]
    return s_delim.join(lst)


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


def warning(color: str = "yellow") -> None:
    """Render/print a failure symbol (almost always in yellow but overrideable)."""
    print(f"[{color}]⚠")


def failure(color: str = "red") -> None:
    """Render/print a failure symbol (almost always in red but overrideable)."""
    print(f"[{color}]✖")


def replace_rich_markup(string: str) -> str:
    """Return a string without Rich markup."""
    return_ = string
    for pattern in re.findall(r"\[.*?\]", string):
        return_ = return_.replace(pattern, "")
    return return_


def message(
    message: str,
    overhead: int = 0,
    color: str = "blue",
    end_success: bool = False,
    end_failure: bool = False,
    end_warning: bool = False,
) -> str:
    """Create and print a message string, padded to width (minus markup) and in the specified color."""
    padding = TERMINAL_WIDTH - overhead - len(replace_rich_markup(message))
    formatted = f"[{color}]{message}{'.' * padding}"

    print(formatted, end="", flush=True)

    if end_success:
        success(color=color)
    elif end_warning:
        warning(color=color)
    elif end_failure:
        failure(color=color)


def v_message(
    verbose: bool,
    s_message: str,
    overhead: int = 0,
    color: str = "blue",
    end_success: bool = False,
    end_failure: bool = False,
    end_warning: bool = False,
) -> str:
    """Create and print a message string AFTER checking for verbosity.

    Essentially, just a wrapper on message to keep the number of verbose conditional
    checks sprinkled throughout to a minimum.
    """
    if verbose:
        message(
            s_message,
            color=color,
            overhead=overhead,
            end_success=end_success,
            end_failure=end_failure,
            end_warning=end_warning,
        )


def run(step: TStep, command: str) -> tuple[bool, str]:  # FIXME: Should be "Step" but will create circular import!
    """Run the command for the specified Step, capturing output and signal success/failure."""
    if step.verbose:
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
    if step.verbose:
        success()
        stdout = result.stdout.decode().strip()
        if stdout:
            print(f"[grey]{stdout}[/]")

    # Most of the time, all we want is whether or not the command was successful but a few
    # methods *need* the actual result of the command for their use, thus, return both!
    return True, result.stdout.decode().strip()


def shorten_path(path, max_length):
    """Shorten a file path to the max length by cutting parent directories off."""
    if len(str(path)) <= max_length:
        return path

    parts = list(path.parts)
    num_parts = len(parts)
    i = num_parts - 1

    total_length = len("...")
    truncated_parts = []
    while total_length + len(parts[i]) + 1 <= max_length and i >= 0:
        truncated_parts.insert(0, parts[i])
        total_length += len(parts[i]) + 1
        i -= 1
    truncated_parts.insert(0, ".../")

    return path.__class__(*truncated_parts)
