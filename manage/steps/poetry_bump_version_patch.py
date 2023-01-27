import sys

from rich import print

from manage.models import Configuration
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Use poetry to do a "patch" level version bump to pyproject.toml"""

    # Use poetry to get what our next version should be:
    success, result = run(step, "poetry version patch --dry-run")
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

    # Update our version in pyproject.toml
    _, result = run(step, "poetry version patch")
    configuration._version = result.split()[-1]
    return True
