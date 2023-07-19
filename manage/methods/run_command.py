"""Run a generic (local) command."""
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import ask_confirm, run


# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(
        name="command",
        type_=str,
        default=None,
    ),
])


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Run a local command."""
    if not (cmd := step.get_arg('command')):
        print("[red]Sorry, we require a 'command' argument for this method.")
        return False

    confirm = f"Ok to run command: '[italic]{cmd}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False

    return run(step, cmd)[0]
