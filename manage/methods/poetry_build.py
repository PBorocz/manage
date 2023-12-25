"""Build a poetry distribution."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes


class Method(AbstractMethod):
    """Build a poetry distribution."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easy single command to build."""
        super().__init__(configuration, recipes, step)
        self.cmd = "poetry build"
        self.confirm = f"Ok to build distribution files? ['[italic]{self.cmd}[/]']"
