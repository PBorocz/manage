"""Verify that poetry.lock is consistent with pyproject.toml and update if not (good security practice)."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import run, warning


class Method(AbstractMethod):
    """Poetry lock check and optional update."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init method."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Poetry lock check and optional update."""
        cmd_chck = "poetry lock --check"  # No changes here, thus, no confirm required!
        cmd_lock = "poetry lock --no-update"  # Dry-run and confirm are possible on this one.

        # Initial check is easy...if it returns fine, we're done...otherwise, update it!
        if not run(self.step, cmd_chck)[0]:
            warning()
            warning("poetry.lock is not consistent with pyproject.toml, attempting fix.")

            if self.configuration.dry_run:
                self.dry_run(cmd_lock)
                return True

            confirm = "Ok to run '[italic]{cmd_lock}[/]' to fix it?"
            if not self.do_confirm(confirm):
                return False

            return run(self.step, cmd_lock)[0]

        return True
