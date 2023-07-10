"""Run a generic (local) command."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Run a local command."""
    if not step.arguments or 'command' not in step.arguments:
        print(f"[red]Sorry, we require a 'command' entry in the arguments for this method.")
        return False

    cmd = step.arguments.get('command')

    if step.confirm:
        if not ask_confirm(f"Ok to run command: [italic]'{cmd}'[/]?"):
            return False

    return run(step, cmd)[0]
