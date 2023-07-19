"""Commits updated files that contain version information locally."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Commits updated files that contain version information locally."""
    confirm = "Ok to commit changes to pyproject.toml and README.*?"
    if step.confirm and not ask_confirm(confirm):
        print(f"To rollback, you may have to set version back to {configuration.version_} re-commit locally.")
        return False
    if not run(step, "git add pyproject.toml README.*")[0]:
        return False
    if not run(step, f'git commit --message "Bump version to {configuration.version}"')[0]:
        return False
    return True
