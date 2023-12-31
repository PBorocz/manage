"""Create git tag, i.e. v<major>.<minor>.<patch>."""
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Create git tag, i.e. v<major>.<minor>.<patch>."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command."""
        super().__init__(__file__, configuration, step)
        tag = self.configuration.version
        self.confirm = f"Ok to create tag in git of '[italic]{tag}[/]'?"
        self.cmd = f"git tag -a {tag} --message {tag}"

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("git"):
            return [msg]
        return []
