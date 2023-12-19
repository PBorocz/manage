"""Build a poetry distribution."""
import shutil

from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import failure, message


class Method(AbstractMethod):
    """Build a poetry distribution."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easy single command to build."""
        super().__init__(configuration, recipes, step)
        self.confirm = f"Ok to build distribution files? ['[italic]{self.cmd}[/]']"
        self.cmd = "poetry build"

        # Check we have a poetry on our path to run against..
        if not shutil.which("poetry"):
            failure()
            message("Sorry, we can't find [italic]poetry[/] on your path.", color="red", end_failure=True)
            return False
