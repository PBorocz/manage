"""Push/publish to PyPI using Poetry."""
import shutil
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import message, failure


class Method(AbstractMethod):
    """Push/publish to PyPI using Poetry."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)
        self.cmd = "poetry publish"
        self.confirm = f"Ok to publish to PyPI with '[italic]{self.cmd}[/]'?"

        # Check we have a poetry on our path to run against..
        if not shutil.which("poetry"):
            failure()
            message("Sorry, we can't find [italic]poetry[/] on your path.", color="red", end_failure=True)
            return False
