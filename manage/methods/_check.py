"""Essentially a no-op."""
from manage.models import Configuration, Recipes


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Don't need to do anything explicit here, stub-only!"""
    return True
