"""Commits updated files that contain version information locally."""
from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import message, run

class Method(AbstractMethod):
    """Commit version-related files."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Commit version-related files."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Commits updated files that contain version information locally."""
        confirm = "Ok to stage & commit changes to pyproject.toml and README.*?"
        if not self.do_confirm(confirm):
            message(f"To rollback, you may have to revert version to {self.configuration.version_} & re-commit.")
            return False

        cmds = (
            "git add pyproject.toml README.*",
            f'git commit --m "Bump version to {self.configuration.version}"',
        )

        for cmd in cmds:
            if self.configuration.dry_run:
                self.dry_run(cmd)
            else:
                if not run(self.step, cmd)[0]:
                    return False
        return True
