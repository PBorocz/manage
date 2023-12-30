"""Method root classes and methods."""
import importlib
import shlex
import subprocess
import sys
from abc import abstractmethod
from pathlib import Path
from typing import Any, TypeVar

from rich import print

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, failure, message, msg_failure, msg_debug, msg_success, success


TClass = TypeVar("Class")


def gather_available_method_classes(debug: bool) -> dict[str, TClass]:
    """Read and return all the python-defined step methods available."""

    def __gather_method_classes():
        """Iterate over all step modules (utility method)."""
        for path in sorted((Path(__file__).parent).glob("*.py")):
            if path.name.startswith("__"):  # Like this very file :-)
                continue

            # Fixme: Should add expection handling here:
            module = importlib.import_module(f"manage.methods.{path.stem}")

            yield path.stem, getattr(module, "Method", None)

    # Get all the 'main" methods in each python file in the steps module:
    classes = {method_name: cls for method_name, cls in __gather_method_classes()}
    if not classes:
        msg_failure("Unable to find [bold]any[/] valid method classes in manage/methods/*.py?")
        sys.exit(1)

    if debug:
        msg_debug(f"{len(classes)} run-time methods found and registered")

    return classes


class AbstractMethod:
    """Abstract SuperClass for all command classes."""

    @abstractmethod
    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """."""
        self.configuration = configuration
        self.recipes = recipes
        self.step = step
        self.cmd: str = None  # Provided on concrete class instantiation
        self.confirm: str = None  # "

    def do_confirm(self, confirm: str | None = None) -> bool:
        """Return True if we're good to keep going and run a command, False otherwise."""
        msg = confirm if confirm else self.confirm

        # If we're running this step in dry_run mode, no need to
        # confirm (this may be duplicative with the run method above
        # BUT this method if more often called on it's own!)
        if self.configuration.dry_run:
            return True

        # Ok, we *ARE* running in in LIVE mode: Do we need to confirm the step?
        if not self.step.confirm:
            return True

        # If we don't have confirmation message, we can't ask for confirmation!
        if not msg:
            return True

        # Finally, does the *USER* want to do the step?
        return ask_confirm(msg)

    def run(self) -> bool:
        """Run a single command after dry-run-check and possible confirmation."""
        if self.configuration.dry_run:
            self.dry_run(self.cmd)
            return True

        if not self.do_confirm():
            return False

        status, _ = self.go(self.cmd)  # Run it for real!
        return status

    ################################################################################
    # Utility methods
    ################################################################################
    def go(self, command) -> tuple[bool, str]:
        """Run the command for the specified Step, return status and stdout/stderr respectively.

        This is here primarily for simple steps that have a single command to be executed for the entire step.
        """
        if self.step.verbose:
            message(f"Running [italic]{command}[/]")

        result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            ################################################
            # Failed:
            ################################################
            # Are we allowed to have error?
            if self.step and not self.step.allow_error:
                if not self.step.verbose:
                    message(f"Running [italic]{command}[/]")
                    failure()
                stderr = result.stderr.decode()
                self.__print_std(stderr, "red")
                return False, stderr

        ################################################
        # Success:
        ################################################
        stdout = result.stdout.decode().strip()
        if self.step.verbose:
            success()
            self.__print_std(stdout, "grey70")
        return True, stdout

    def __print_std(self, std: str, color: str) -> None:
        if not std:
            return
        for line in std.strip().split("\n"):
            print(f"[{color}]≫ {line}[/]")

    def dry_run(self, cmd: str) -> None:
        """Wrap-up format for dry-run command messages."""
        msg_success(f"DRY-RUN -> '{cmd}'")

    def get_arg(self, arg_name: str, optional: bool = False, default: Any | None = None) -> str | None:
        """Find the value of the specified argument in the step, else look for default."""
        if arg_value := self.step.get_arg(arg_name):
            return arg_value

        # No value found, do we have a default to return?
        if default:
            return default

        # If the argument is OPTIONAL, we're OK to return None..
        if optional:
            return None

        # Otherwise, we expected to find an argument and no default was provided!!
        msg_failure(f"Sorry, command requires a supplemental argument for '{arg_name}'")
        return None

    def validate_pathspec(self, cls: str, arg: str) -> list | None:
        """Perform a validation of a 'pathspec' parameter.

        We define this here as there are several method-classes that use
        this logic.
        """
        if pathspec := self.configuration.find_method_arg_value(cls, arg):
            if not Path(pathspec).exists():
                return [f"({cls}:{arg}) '[italic]{pathspec}[/]' does not exist."]
        return None
