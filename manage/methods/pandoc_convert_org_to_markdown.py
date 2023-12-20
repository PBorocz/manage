"""Convert an emacs org file into a markdown version using Pandoc."""
from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import failure, message, run


# Metadata about arguments available...
args = Arguments(
    arguments=[
        Argument(
            name="path_org",
            type_=str,
            default=None,
        ),
        Argument(
            name="path_md",
            type_=str,
            default=None,
        ),
    ],
)


class Method(AbstractMethod):
    """Convert an emacs org file into a markdown version using Pandoc."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Run pandoc.."""
        # Lookup arguments
        if not (path_md := self.get_arg("path_md")):
            return False

        if not (path_org := self.get_arg("path_org")):
            return False

        # Get our command and confirmation string:
        cmd = f"pandoc -f org -t markdown-smart --wrap none --output {path_md} {path_org}"
        confirm = f"Ok to run '[italic]{cmd}[/]'?"

        # Dry-run?
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        # Confirm?
        if not self.do_confirm(confirm):
            return False

        try:
            return run(self.step, cmd)[0]
        except FileNotFoundError:
            failure()
            message("Sorry, perhaps couldn't find a [italic]pandoc[/] executable on your path?", color="red")
            return False
