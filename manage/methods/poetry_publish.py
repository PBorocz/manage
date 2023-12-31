"""Push/publish to PyPI using Poetry."""
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Push/publish to PyPI using Poetry."""

    def __init__(self, configuration: Configuration, step: dict):
        """Init."""
        super().__init__(__file__, configuration, step)
        self.cmd = "poetry publish"
        self.confirm = f"Ok to publish to PyPI with '[italic]{self.cmd}[/]'?"

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("poetry"):
            return [msg]
        return []
