"""Build a poetry distribution."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, message, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Build a poetry distribution."""
    cmd = "poetry build"

    confirm = f"Ok to build distribution files with '[italic]{cmd}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False

    if configuration.dry_run and not configuration.live:
        msg = f"DRY-RUN -> '{cmd}'"
        message(msg, color="green", end_success=True)
        return True
    else:
        return run(step, cmd)[0]
