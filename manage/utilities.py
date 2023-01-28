"""Utility methods, not meant for direct calling from manage.toml."""
import shlex
import subprocess
import sys

from rich import print
from rich.console import Console

from manage.models import Step

TERMINAL_WIDTH = 70


def smart_join(lst: list[str]) -> str:
    """Essentially ', ' but with nicer formatting."""
    return ', '.join(lst[:-1]) + " or " + lst[-1]


def ask_confirm(text: str) -> bool:
    """Ask for confirmation, returns True if "yes" answer, False otherwise"""
    while True:
        prompt = fmt(f"{text} (y/N)", color="#fffc00")
        answer = Console().input(prompt).lower()
        if answer in ("n", "no", ""):
            return False
        elif answer in ("y", "yes"):
            return True


def success() -> None:
    """Render/print a success symbol."""
    print("[green]✔")


def failure() -> None:
    """Render/print a failure symbol."""
    print("[red]✖")


def fmt(message: str, overhead: int = 0, color: str = 'blue') -> str:
    """Pad the message string to width (net of overhead) and in the specified color (if possible)."""
    padding = TERMINAL_WIDTH - overhead - len(message)
    return f"[{color}]{message}{'.' * padding}"


def run(step: Step, command: str) -> tuple[bool, str]:
    """Run the command for the specified Step, capturing output and signalling success/failure."""
    if not step.quiet_mode:
        msg = fmt(f"Running [italic]{command}[/italic]", overhead=-17)
        print(msg, flush=True, end="")

    result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        ################################################
        # Failed:
        ################################################
        # Are we allowed to have error?
        if step and not step.allow_error:
            failure()
            sys.stderr.print(result.stderr.decode())
            return False, result.stderr.decode()

    ################################################
    # Success:
    ################################################
    if not step.quiet_mode:
        success()
        if step.echo_stdout:
            print(result.stdout.decode().strip())

    return True, result.stdout.decode().strip()
