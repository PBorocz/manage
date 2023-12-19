"""Create git tag, i.e. v<major>.<minor>.<patch>."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes


class Method(AbstractMethod):
    """Create git tag, i.e. v<major>.<minor>.<patch>."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Easy single command."""
        super().__init__(configuration, recipes, step)
        tag = self.configuration.version
        self.confirm = f"Ok to create tag in git of '[italic]{tag}[/]'?"
        self.cmd = f"git tag -a {tag} --message {tag}"
