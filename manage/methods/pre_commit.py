"""Run pre-commit."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes


class Method(AbstractMethod):
    """Run pre-commit."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easy single command to run pre-commit."""
        super().__init__(configuration, recipes, step)
        self.cmd = "pre-commit run --all-files"
        self.confirm = None
