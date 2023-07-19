"""Run pre-commit."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Run pre-commit."""
    return run(step, "pre-commit run --all-files")[0]
