"""Essentially a no-op."""

from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import message


class Method(AbstractMethod):
    """Show/print the recipes."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easiest method as we already did validation before we got here!"""
        super().__init__(configuration, recipes, step)

    def run(self):
        """Override and use our local run method since there's no actual command to print."""
        message("All checks complete, no issues found", color="green", end_success=True)
        return True
