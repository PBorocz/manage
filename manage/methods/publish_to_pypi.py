"""Push/publish to PyPI using Poetry."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Push/publish to PyPI using Poetry."""
    cmd = "poetry publish"
    confirm = f"Ok to publish to PyPI with '[italic]{cmd}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False
    return run(step, cmd)[0]
