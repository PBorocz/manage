"""Method to run SASS pre-processor."""
from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import run


# Metadata about arguments available...
args = Arguments(
    arguments=[
        Argument(
            name="pathspec",
            type_=str,
            default=None,
        ),
    ],
)


class Method(AbstractMethod):
    """Run a SASS pre-processor command on the required pathspec."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Do it."""
        # Lookup argument and get resultant command:
        if not (pathspec := self.get_arg("pathspec")):
            return False
        cmd = f"sass {pathspec}"

        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        if not self.do_confirm(f"Ok to run '[italic]{cmd}[/]'?"):
            return False

        return run(self.step, cmd)[0]
