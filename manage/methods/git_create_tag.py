"""Create git tag, i.e. v<major>.<minor>.<patch>."""
import shutil
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Create git tag, i.e. v<major>.<minor>.<patch>."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command."""
        super().__init__(__file__, configuration, step)
        tag = self.configuration.version
        self.confirm = f"Ok to create tag in git of '[italic]{tag}[/]'?"
        self.cmd = f"git tag -a {tag} --message {tag}"

    def validate(self) -> None:
        """Perform any pre-method validation."""
        # Check to see if executable is available
        exec_ = "git"
        if not shutil.which(exec_):
            msg = f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method."
            self.exit_with_fails([msg])
