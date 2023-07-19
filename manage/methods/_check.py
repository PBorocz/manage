"""Essentially a no-op."""
from manage.models import Configuration, Recipes
from manage.utilities import message


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Don't need to do anything explicit here, stub-only!"""
    message("All checks complete, no issues found", color="green", end_success=True)
    return True
