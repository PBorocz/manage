"""Clean step."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Clean the build environment."""
    cmd = "rm -rf build *.egg-info"
    confirm = f"Ok to clean build environment with '[italic]{cmd}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False
    return run(step, cmd)[0]
