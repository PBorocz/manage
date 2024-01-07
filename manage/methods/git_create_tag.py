"""Create git tag, i.e. v<major>.<minor>.<patch>."""
from manage.methods import AbstractMethod
from manage.models import Configuration, PyProject


class Method(AbstractMethod):
    """Create git tag, i.e. v<major>.<minor>.<patch>."""

    def __init__(self, configuration: Configuration, step: dict):
        """Easy single command, using most current version in pyproject.toml."""
        super().__init__(__file__, configuration, step)
        pyproject: PyProject = PyProject.factory()
        v_version = f"v{pyproject.version}"  # Use the vM.m.p format for the version here..
        self.confirm = f"Ok to create tag in git of '[italic]{v_version}[/]'?"
        self.cmd = f"git tag -a {v_version} --message {v_version}"

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("git"):
            return [msg]
        return []
