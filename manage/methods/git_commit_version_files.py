"""Commits updated files that contain version information locally."""

from manage.methods import AbstractMethod
from manage.models import Configuration
from manage.utilities import message


class Method(AbstractMethod):
    """Commit version-related files."""

    def __init__(self, configuration: Configuration, step: dict):
        """Commit version-related files."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("git"):
            return [msg]
        return []

    def run(self) -> bool:
        """Commits updated files that contain version information locally."""
        cmds = (
            "git add pyproject.toml README.*",
            f'git commit --m "Bump version to {self.configuration.version}"',
        )

        # Dry-run?
        if self.configuration.dry_run:
            for cmd in cmds:
                self.dry_run(cmd)
            return True

        # Confirmation
        confirm = "Ok to stage & commit changes to pyproject.toml and README.*?"
        if not self.do_confirm(confirm):
            message(f"To rollback, you may have to revert version to {self.configuration.version_} & re-commit.")
            return False

        # Do em!
        for cmd in cmds:
            status, _ = self.go(cmd)
            if not status:
                return False
        return True
