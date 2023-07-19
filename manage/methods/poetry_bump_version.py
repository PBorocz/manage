"""Manage step."""
import sys

from rich import print

from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import ask_confirm, failure, run, smart_join

POETRY_VERSIONS = ('patch', 'minor', 'major', 'prepatch', 'preminor', 'premajor', 'prerelease')

# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(
        name="poetry_version",
        type_=str,
        default="bump",
    ),
])

def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Do a version "bump" of pyproject.toml using poetry by a specified "level"."""
    if not (poetry_version := step.get_arg('poetry_version')):
        print("[red]Sorry, this command requires supplemental argument: poetry_version")
        sys.exit(1)

    if poetry_version not in POETRY_VERSIONS:
        versions = smart_join(POETRY_VERSIONS, with_or=True)
        print(f"[red]Sorry, {poetry_version} is not a valid poetry_version, must be one of \\[{versions}].")
        sys.exit(1)

    # Use poetry to get what our next version *should* be (NOTE: This is a DRY-RUN only!!!!)
    success, result = run(step, f"poetry version {poetry_version} --dry-run")
    if not success:
        failure()
        print(f"[red]Sorry, Poetry couldn't determine a new version number from pyproject.toml: {result}")
        sys.exit(1)

    new_version = result.split()[-1]  # a bit fragile, we're relying on poetry default message format :-(

    ################################################################################
    # Safety check
    ################################################################################
    confirm = f"Ok to bump version from '[italic]{configuration.version}[/]' to '[italic]v{new_version}[/]' in pyproject.toml?"
    if step.confirm and not ask_confirm(confirm):
        return False

    # Update our version in pyproject.toml
    result = run(step, f"poetry version {poetry_version}")[1]
    configuration.version_ = result.split()[-1]
    configuration.version = f"v{configuration.version_}" # FIXME: Duplicate with models.py/configuration_factory!
    return True
