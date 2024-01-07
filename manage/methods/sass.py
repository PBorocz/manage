"""Method to run SASS pre-processor."""
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

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        fails = []

        # Check to see if executable is available
        if msg := self.validate_executable("sass"):
            fails += msg

        # Check to make sure argument is provided
        if not (pathspec := self.get_arg("pathspec")):
            fails += f"Sorry, The {self.name} method requires a [italic]pathspec[/] argument."

        # Check to make sure path(s) provided actually exist on disk
        if msgs := self.validate_pathspec(Path(__file__).stem, pathspec):
            fails.extend(msgs)

        return fails

    def run(self) -> bool:
        """Do it."""
        # Lookup argument and get resultant command:
        pathspec = self.get_arg("pathspec")

        cmd = f"sass {pathspec}"

        if self.configuration.dry_run:
            self.dry_run(cmd, shell=True)
            return True

        if not self.do_confirm(f"Ok to run '[italic]{cmd}[/]'?"):
            return False

        return self.go(cmd)[0]
