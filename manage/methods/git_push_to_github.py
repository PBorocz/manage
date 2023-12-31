"""Push to github."""
import shutil

from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Push to github."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to push."""
        super().__init__(__file__, configuration, step)
        self.confirm = "Ok to push to github?"
        self.cmd = "git push --follow-tags"

    def validate(self) -> None:
        """Perform any pre-method validation."""
        # Check to see if executable is available
        exec_ = "git"
        if not shutil.which(exec_):
            msg = f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method."
            self.exit_with_fails([msg])
