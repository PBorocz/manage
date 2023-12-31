"""Push/publish to PyPI using Poetry."""
import shutil
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Push/publish to PyPI using Poetry."""

    def __init__(self, configuration: Configuration, step: dict):
        """Init."""
        super().__init__(__file__, configuration, step)
        self.cmd = "poetry publish"
        self.confirm = f"Ok to publish to PyPI with '[italic]{self.cmd}[/]'?"

    def validate(self) -> None:
        """Perform any pre-method validation."""
        # Check to see if executable is available
        exec_ = "poetry"
        if not shutil.which(exec_):
            msg = f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method."
            self.exit_with_fails([msg])
