"""Build a poetry distribution."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Build a poetry distribution."""
    cmd = "poetry build"
    confirm = f"Ok to build distribution files with '[italic]{cmd}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False
    return run(step, "poetry build")[0]
