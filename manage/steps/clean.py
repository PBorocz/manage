"""Clean step"""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Clean the build environment."""
    if step.confirm and not step.quiet_mode:
        if not ask_confirm("Ok to clean build environment?"):
            return False
    return run(step, "rm -rf build *.egg-info")[0]
