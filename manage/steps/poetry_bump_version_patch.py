import sys

from rich import print

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run, smart_join

POETRY_VERSIONS = ('patch', 'minor', 'major', 'prepatch', 'preminor', 'premajor', 'prerelease')


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Do a version "bump" of pyproject.toml using poetry by a specified "level"."""
    if not step.arguments or 'poetry_version' not in step.arguments:
        print("[red]Sorry, this command requires supplemental argument: poetry_version")
        sys.exit(1)

    poetry_version = step.arguments.get('poetry_version')
    breakpoint()

    if poetry_version not in POETRY_VERSIONS:
        print(f"[red]Sorry, {poetry_version} is not a valid poetry_version, must be one of: {smart_join(POETRY_VERSIONS)}")
        sys.exit(1)

    # FIXME: Do we want to validate the poetry_version provided to one of the following?
    #        patch, minor, major, prepatch, preminor, premajor, prerelease.

    # Use poetry to get what our next version *should* be:
    success, result = run(step, f"poetry version {poetry_version} --dry-run")
    if not success:
        print(f"[red]Sorry, Poetry couldn't determine a new version number from pyproject.toml: {result}")
        sys.exit(1)
    new_version = result.split()[-1]  # a bit fragile, we're relying on poetry default message format :-(

    ################################################################################
    # Safety check
    ################################################################################
    if step.confirm:
        if not ask_confirm(f"Ok to bump version from {configuration.version()} to v{new_version} in pyproject.toml?"):
            return False
    breakpoint()

    # Update our version in pyproject.toml
    _, result = run(step, f"poetry version {poetry_version}")
    configuration.version_ = result.split()[-1]
    return True
