"""Verify that poetry.lock is consistent with pyproject.toml and update if not (good security practice)."""
from manage.methods import AbstractMethod
from manage.models import Configuration
from manage.utilities import msg_warning, warning


class Method(AbstractMethod):
    """Poetry lock check and optional update."""

    def __init__(self, configuration: Configuration, step: dict):
        """Init method."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        if msg := self.validate_executable("poetry"):
            return [msg]
        return []

    def run(self) -> bool:
        """Poetry lock check and optional update."""
        cmd_chck = "poetry lock --check"  # No changes here, thus, no confirm required!
        cmd_lock = "poetry lock --no-update"  # Dry-run and confirm are possible on this one.

        # Initial check is easy...if it returns fine, we're done...otherwise, update it!
        if not self.go(cmd_chck)[0]:
            warning()
            msg_warning("poetry.lock is not consistent with pyproject.toml, attempting fix.")

            if self.configuration.dry_run:
                self.dry_run(cmd_lock, shell=True)
                return True

            confirm = "Ok to run '[italic]{cmd_lock}[/]' to fix it?"
            if not self.do_confirm(confirm):
                return False

            return self.go(cmd_lock)[0]

        return True
