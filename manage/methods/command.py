"""Run a generic (local) command."""
from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration


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

    def __init__(self, configuration: Configuration, step: dict):
        """Init."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        # Check to make sure argument is provided
        if not self.get_arg("command"):
            return [f"Sorry, The {self.name} method requires a [italic]command[/] argument."]
        return []

    def run(self) -> bool:
        """Run a local command."""
        # Get argument...
        command = self.get_arg("command")

        if self.configuration.dry_run:
            self.dry_run(command)
            return True

        if self.do_confirm(f"Ok to run command: '[italic]{command}[/]'?"):
            return False

        return self.go(command)[0]
