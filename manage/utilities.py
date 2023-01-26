"""Utility methods, not meant for direct calling from manage.toml."""
import shlex
import subprocess
from typing import Optional

from rich import print
from rich.console import Console

from models import Configuration

TERMINAL_WIDTH = 70


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


def run(step: Optional[dict], command: str) -> tuple[bool, str]:
    """Run the command for the specified (albeit optional) step, capturing output and signalling success/failure."""
    msg = fmt(f"Running [italic]{command}[/italic]", overhead=-17)
    print(msg, flush=True, end="")

    result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        # Command failed, are we allowed to have errors?
        if step and not step.get("allow_error", False):
            failure()
            print(result.stderr.decode())
            return False, result.stderr.decode()
    # Command succeeded Ok.
    success()
    if step and step.get("echo_stdout", False):
        print(result.stdout.decode().strip())

    return True, result.stdout.decode().strip()


def dispatch(configuration: Configuration, recipes: dict, target: str) -> None:
    """Iterate (ie. execute) each step in the selected target's recipes for the specified package."""

    for step in recipes.get(target).get("steps"):
        assert "step" in step or "method" in step, f"Sorry, one of '{target}'s steps is missing 'step' or 'method'."

        # This step could be either a request to invoke a particular method OR a request to run another step
        if "step" in step:
            # Run another step
            dispatch(step.get("step"), recipes)

        elif "method" in step:
            # Lookup and run the method associated with the step:
            method_name = step.get("method")
            method = recipes.get("__step_callables__").get(method_name)
            if method is None:
                raise RuntimeError(f"Sorry, unable to find method: '{method_name}'")
            method(step)
