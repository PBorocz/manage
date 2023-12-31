"""Method to run SASS pre-processor."""
import shutil
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration


class Method(AbstractMethod):
    """Run a SASS pre-processor command on the required pathspec."""

    args = Arguments(
        arguments=[
            Argument(
                name="pathspec",
                type_=str,
                default=None,
            ),
        ],
    )

    def __init__(self, configuration: Configuration, step: dict):
        """Init."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> None:
        """Perform any pre-method validation."""
        fails = []

        # Check to see if executable is available
        exec_ = "sass"
        if not shutil.which(exec_):
            fails.append(f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method.")

        # Check to make sure argument is provided
        if not (pathspec := self.get_arg("pathspec")):
            fails.append(f"Sorry, The {self.name} method requires a [italic]pathspec[/] argument.")

        # Check to make sure argument provided actually exists on disk
        elif not Path(pathspec).exists():
            fails.append(f"Sorry, path '[italic]{pathspec}[/]' could not be found for the {self.name} method.")

        if fails:
            self.exit_with_fails(fails)

        return fails

    def run(self) -> bool:
        """Do it."""
        # Lookup argument and get resultant command:
        pathspec = self.get_arg("pathspec")

        cmd = f"sass {pathspec}"

        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        if not self.do_confirm(f"Ok to run '[italic]{cmd}[/]'?"):
            return False

        return self.go(cmd)[0]
