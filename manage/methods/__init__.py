"""Method root classes and methods."""
from abc import ABC, abstractmethod

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
        self.cmd: str = None      # Provided on concrete class instantiation
        self.confirm: str = None  # "

    def run(self) -> bool:
        """Run a single command after possible confirmation and dry-run check."""
        if self.configuration.dry_run:
            self.dry_run(self.cmd)
            return True

        if self.step.confirm:                      # Do we need to do a confirm?
            if self.confirm:                       # Do we *have* a confirm message?
                if not ask_confirm(self.confirm):  # Did the user want to pass on it?
                    return False

        # Otherwise, run it!
        result, _ = run(self.step, self.cmd)
        return result

    def do_confirm(self, confirm: str | None = None) -> bool:
        """."""
        msg = confirm if confirm else self.confirm

        # If we're running this step in dry_run mode, no need to confirm!
        if self.configuration.dry_run:
            return True

        # Running in LIVE mode, do we need to confirm for the step?
        if not self.step.confirm:             # Do we need to do a confirm?
            return True

        # *DO* we have a confirm message"
        if not msg:
            return True

        # Does the user still want to do the action?
        if not ask_confirm(msg):
            return False
        return True

    def dry_run(self, msg: str) -> None:
        """Wrap-up format for dry-run command messages."""
        message(f"DRY-RUN -> '{msg}'", end_success=True, color="green")
