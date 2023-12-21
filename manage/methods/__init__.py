"""Method root classes and methods."""
import importlib
import sys
from abc import abstractmethod
from pathlib import Path
from typing import Any, TypeVar

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, failure, message, run, success


TClass = TypeVar("Class")


def gather_available_method_classes(verbose: bool) -> dict[str, TClass]:
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
    if verbose:
        message("Initialising methods available")

    classes = {method_name: cls for method_name, cls in __gather_method_classes()}
    if not classes:
        failure()
        print("[red]Unable to find [bold]any[/] valid method classes in manage/methods/*.py?")
        sys.exit(1)

    if verbose:
        success()
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

    def run(self) -> bool:
        """Run a single command after dry-run-check and possible confirmation."""
        if self.configuration.dry_run:
            self.dry_run(self.cmd)
            return True

        if not self.do_confirm():
            return False

        status, _ = run(self.step, self.cmd)  # Run it for real!
        return status

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

    ################################################################################
    # Utility methods
    ################################################################################
    def dry_run(self, cmd: str) -> None:
        """Wrap-up format for dry-run command messages."""
        message(f"DRY-RUN -> '{cmd}'", end_success=True, color="green")

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
        message(f"Sorry, command requires a supplemental argument for '{arg_name}'", color="red", end_failure=True)
        return None
