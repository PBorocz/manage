"""Method root classes and methods."""
from abc import abstractmethod
from typing import Any

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, message, run


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
        # BUT this method if most often called on it's own!)
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
