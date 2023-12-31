"""Clean step."""
from manage.methods import AbstractMethod
from manage.models import Configuration


class Method(AbstractMethod):
    """Clean up build artifacts."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command to clean."""
        super().__init__(__file__, configuration, step)
        self.cmd = "rm -rf build *.egg-info"
        self.confirm = f"Ok to clean build environment with '[italic]{self.cmd}[/]'?"
