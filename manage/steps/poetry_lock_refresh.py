"""Refresh poetry.lock file (good security practice)."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Poetry lock refresh."""
    if step.confirm:
        if not ask_confirm("Ok to refresh poetry.lock from pyproject.toml?"):
            return False
    return run(step, "poetry lock --no-update")[0]
