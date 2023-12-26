"""Manage step."""
import sys

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import failure, message, smart_join

BUMP_RULES = ("patch", "minor", "major", "prepatch", "preminor", "premajor", "prerelease")


class Method(AbstractMethod):
    """Do a version "bump" of pyproject.toml using poetry by a specified "level"."""

    args = Arguments(
        arguments=[
            Argument(
                name="bump_rule",
                type_=str,
                default="bump",
            ),
        ],
    )

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Init."""
        super().__init__(configuration, recipes, step)

    def validate(self) -> list | None:
        """Perform any pre-step validation."""
        if bump_rule := self.configuration.method_args.get("bump_rule"):
            if bump_rule not in BUMP_RULES:
                versions = smart_join(BUMP_RULES, with_or=True)
                return [f"(poetry_version) '[italic]{bump_rule}[/]' is not a valid bump_rule: \\[{versions}]."]
        return None

    def run(self) -> bool:
        """Do a version "bump" of pyproject.toml using poetry to a specified poetry "level"."""
        # Get argument
        if not (bump_rule := self.get_arg("bump_rule")):
            return False

        cmd = f"poetry version {bump_rule}"

        ################################################################################
        # Dry-run?
        ################################################################################
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        ################################################################################
        # For confirmation purposes, use poetry to get what our next
        # version *should* be (NOTE: This is a DRY-RUN only!!!!)
        ################################################################################
        success, new_version = self.go(f"{cmd} --dry-run --short")
        if not success:
            failure()
            msg = (
                "Sorry, poetry couldn't determine a new "
                f"version number from pyproject.toml: [italic]{new_version}[/]"
            )
            message(msg)
            sys.exit(1)

        confirm = (
            f"Ok to '[italic]{self.configuration.version}[/]' "
            f"to '[italic]v{new_version}[/]' in pyproject.toml? "
            f"'[italic]{cmd}[/]'"
        )
        if not self.do_confirm(confirm):
            return False

        ################################################################################
        # Run it by doing the REAL poetry version!
        ################################################################################
        status, output = self.go(cmd)
        if status:
            # Side-effect! -> Make sure our configuration has the NEW version from now on!
            self.configuration.set_version(output.split()[-1])
            return True
        else:
            return False
