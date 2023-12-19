"""Clean step."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes

class Method(AbstractMethod):
    """Clean up build artifacts."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easy single command to clean."""
        super().__init__(configuration, recipes, step)
        self.cmd = "rm -rf build *.egg-info"
        self.confirm = f"Ok to clean build environment with '[italic]{self.cmd}[/]'?"
