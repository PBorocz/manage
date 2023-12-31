"""Run pre-commit."""
import shutil

from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Run pre-commit."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to run pre-commit."""
        super().__init__(__file__, configuration, step)
        self.cmd = "pre-commit run --all-files"
        self.confirm = None

    def validate(self) -> None:
        """Perform any pre-method validation."""
        # Check to see if executable is available
        exec_ = "pre-commit"
        if not shutil.which(exec_):
            msg = f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method."
            self.exit_with_fails([msg])
