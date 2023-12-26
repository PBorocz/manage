"""Convert an emacs org file into a markdown version using Pandoc."""
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import failure, message, success


class Method(AbstractMethod):
    """Convert an emacs org file into a markdown version using Pandoc."""

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

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)

    def validate(self) -> list | None:
        """Perform any pre-step validation."""
        if path_md := self.configuration.method_args.get("path_md"):
            if not Path(path_md).exists():
                return [f"Sorry, '[italic]{path_md}[/]' does not exist."]
        return None

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
            if self.step.verbose:
                message(f"Running [italic]{cmd}[/]")
            status, _ = self.go(cmd)
            if self.step.verbose:
                if not status:
                    failure()
                else:
                    success()
        except FileNotFoundError:
            failure()
            message("Sorry, perhaps couldn't find a [italic]pandoc[/] executable on your path?", color="red")
            return False
        finally:
            return status
