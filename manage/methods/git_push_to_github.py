"""Push to github."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes


class Method(AbstractMethod):
    """Push to github."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easy single command to push."""
        super().__init__(configuration, recipes, step)
        self.confirm = "Ok to push to github?"
        self.cmd = "git push --follow-tags"
