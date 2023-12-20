"""Push/publish to PyPI using Poetry."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes


class Method(AbstractMethod):
    """Push/publish to PyPI using Poetry."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)
        self.cmd = "poetry publish"
        self.confirm = f"Ok to publish to PyPI with '[italic]{self.cmd}[/]'?"
