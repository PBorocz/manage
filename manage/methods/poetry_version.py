"""Manage step."""
import sys
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, PyProject
from manage.utilities import failure, message, smart_join

BUMP_RULES = ("patch", "minor", "major", "prepatch", "preminor", "premajor", "prerelease")


class Method(AbstractMethod):
    """Do a version "bump" of pyproject.toml using poetry by a specified "level"."""

    args = Arguments(
        arguments=[
            Argument(
                name="bump_rule",
                type_=str,
                default="patch",
            ),
        ],
    )

    def __init__(self, configuration: Configuration, step: dict):
        """Init."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        fails = []

        # Check to see if executable is available
        if msg := self.validate_executable("poetry"):
            fails.append(msg)

        if bump_rule := self.configuration.find_method_arg_value(Path(__file__).stem, "bump_rule"):
            if bump_rule not in BUMP_RULES:
                versions = smart_join(BUMP_RULES, with_or=True)
                fails.append(f"(poetry_version) '[italic]{bump_rule}[/]' is not a valid bump_rule: \\[{versions}].")

        return fails

    def run(self) -> bool:
        """Do a version "bump" of pyproject.toml using poetry to bump up to a specified poetry "level"."""
        # Get argument
        if not (bump_rule := self.get_arg("bump_rule")):
            return False

        pyproject: PyProject = PyProject.factory()
        v_old_version = f"v{pyproject.version}"

        cmd = f"poetry version {bump_rule}"

        ################################################################################
        # For confirmation purposes, use poetry to get what our next
        # version *should* be (NOTE: This is a DRY-RUN only!!!!)
        ################################################################################
        success, new_version_or_error = self.go(f"{cmd} --dry-run --short")
        if not success:
            failure()
            msg = (
                "Sorry, poetry couldn't determine a new version number "
                f"from pyproject.toml: [italic]{new_version_or_error}[/]"
            )
            message(msg)
            sys.exit(1)

        ################################################################################
        # Dry-run?
        ################################################################################
        if self.configuration.dry_run:
            self.dry_run(cmd, shell=True)
            return True

        confirm = (
            f"Ok to upgrade from '[italic]{v_old_version}[/]' "
            f"to '[italic]v{new_version_or_error}[/]' in pyproject.toml? "
            f"'[italic]{cmd}[/]'"
        )
        if not self.do_confirm(confirm):
            return False

        ################################################################################
        # Run it by doing the REAL poetry version!
        ################################################################################
        status, _ = self.go(cmd)
        if status:
            return True
        return False
