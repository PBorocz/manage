"""Verify that poetry.lock is consistent with pyproject.toml (good security practice)."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Poetry lock check."""
    return run(step, "poetry lock --check")[0]
