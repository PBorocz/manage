"""Build a poetry distribution."""
import shutil
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Build a poetry distribution."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to build."""
        super().__init__(__file__, configuration, step)
        self.cmd = "poetry build"
        self.confirm = f"Ok to build distribution files? ['[italic]{self.cmd}[/]']"

    def validate(self) -> None:
        """Perform any pre-method validation."""
        # Check to see if executable is available
        exec_ = "poetry"
        if not shutil.which(exec_):
            msg = f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method."
            self.exit_with_fails([msg])
