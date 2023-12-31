"""Build a poetry distribution."""
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Build a poetry distribution."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to build."""
        super().__init__(__file__, configuration, step)
        self.cmd = "poetry build"
        self.confirm = f"Ok to build distribution files? ['[italic]{self.cmd}[/]']"

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("poetry"):
            return [msg]
        return []
