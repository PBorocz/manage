"""Manage step."""
import sys

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import failure, message, run, smart_join

POETRY_VERSIONS = ("patch", "minor", "major", "prepatch", "preminor", "premajor", "prerelease")

# Metadata about arguments available...
args = Arguments(
    arguments=[
        Argument(
            name="poetry_version",
            type_=str,
            default="bump",
        ),
    ],
)


class Method(AbstractMethod):
    """Do a version "bump" of pyproject.toml using poetry by a specified "level"."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Do a version "bump" of pyproject.toml using poetry by a specified "level"."""
        # Get argument...
        if not (poetry_version := self.get_arg("poetry_version")):
            return False

        # FIXME: Can we put this into our validation check? Perhaps as a local method that's called earlier?
        if poetry_version not in POETRY_VERSIONS:
            versions = smart_join(POETRY_VERSIONS, with_or=True)
            failure()
            message(f"[red]Sorry, {poetry_version} is not a valid poetry_version, must be one of \\[{versions}].")
            sys.exit(1)

        # The arg becomes the core command to execute:
        cmd = f"poetry version {poetry_version}"

        ################################################################################
        # For confirmation purposes, use poetry to get what our next
        # version *should* be (NOTE: This is a DRY-RUN only!!!!)
        ################################################################################
        success, result = run(self.step, f"poetry version {poetry_version} --dry-run")
        if not success:
            failure()
            msg = (
                "[red]Sorry, poetry couldn't determine a new "
                f"version number from pyproject.toml: [italic]{result}[/]"
            )
            message(msg)
            sys.exit(1)
        new_version = result.split()[-1]  # a bit fragile, we're relying on poetry default message format :-(

        confirm = (
            f"Ok to '[italic]{self.configuration.version}[/]' "
            f"to '[italic]v{new_version}[/]' in pyproject.toml? "
            f"'[italic]{cmd}[/]'"
        )
        if not self.do_confirm(confirm):
            return False

        ################################################################################
        # Dry-run?
        ################################################################################
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        ################################################################################
        # Run it AND save the new version that poetry gave us!
        ################################################################################
        status, output = run(self.step, cmd)
        if status:
            # Side-effect! -> Make sure our configuration has the NEW version from now on!
            self.configuration.set_version(output.split()[-1])
            return True
        else:
            return False
