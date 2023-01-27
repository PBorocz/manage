from rich import print

from manage.models import Configuration
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Commits updated files that contain version information locally."""
    msg = "Ok to commit changes to pyproject.toml and README.org?"
    if step.confirm:
        if not ask_confirm(msg):
            print(f"To rollback, you may have to set version back to {configuration._version} re-commit locally.")
            return False
    if not run(step, "git add pyproject.toml README.org")[0]:
        return False
    if not run(step, f'git commit --message "Bump version to {configuration.version()}"')[0]:
        return False
    return True
