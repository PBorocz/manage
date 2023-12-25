"""Run a generic (local) command."""
from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes


class Method(AbstractMethod):
    """Run a generic (local) command."""

    args = Arguments(
        arguments=[
            Argument(
                name="command",
                type_=str,
                default=None,
            ),
        ],
    )

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Run a local command."""
        # Get argument...
        if not (command := self.get_arg("command")):
            return False

        if self.configuration.dry_run:
            self.dry_run(command)
            return True

        if self.do_confirm(f"Ok to run command: '[italic]{command}[/]'?"):
            return False

        return self.go(command)[0]
