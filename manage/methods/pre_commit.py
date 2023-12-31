"""Run pre-commit."""

from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Run pre-commit."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to run pre-commit."""
        super().__init__(__file__, configuration, step)
        self.cmd = "pre-commit run --all-files"
        self.confirm = None

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("pre-commit"):
            return [msg]
        return []
