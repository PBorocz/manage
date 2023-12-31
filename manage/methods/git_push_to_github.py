"""Push to github."""

from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Push to github."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to push."""
        super().__init__(__file__, configuration, step)
        self.confirm = "Ok to push to github?"
        self.cmd = "git push --follow-tags"

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("git"):
            return [msg]
        return []
