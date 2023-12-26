"""Utility methods, not meant for direct calling from manage.toml."""
import re
import sys
from typing import Final

from rich import print
from rich.console import Console


TERMINAL_WIDTH: Final = 79


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


################################################################################
# "messaging" support methods
################################################################################
def success(color: str = "green") -> None:
    """Render/print a success symbol (almost always in green but overrideable)."""
    print(f"[{color}]✔")


def warning(color: str = "yellow") -> None:
    """Render/print a failure symbol (almost always in yellow but overrideable)."""
    print(f"[{color}]⚠")


def failure(color: str = "red") -> None:
    """Render/print a failure symbol (almost always in red but overrideable)."""
    print(f"[{color}]✖")


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


def msg_warning(msg: str) -> None:
    """Wrap message method obo a Warning."""
    message(msg, color="yellow", end_warning=True)


def msg_failure(msg: str) -> None:
    """Wrap message method obo a Failure."""
    message(msg, color="red", end_failure=True)


def msg_success(msg: str) -> None:
    """Wrap message method obo a simple success message."""
    message(msg, color="green", end_success=True)


def msg_debug(msg: str) -> None:
    """Wrap message method obo a simple debug message."""
    message(msg, color="light_slate_grey", end_success=True)


def replace_rich_markup(string: str) -> str:
    """Return a string without Rich markup."""
    return_ = string
    for pattern in re.findall(r"\[.*?\]", string):
        return_ = return_.replace(pattern, "")
    return return_


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
