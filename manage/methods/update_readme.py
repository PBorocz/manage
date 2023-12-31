"""Change the local README to update the version number (and date) for Unreleased changes."""
from datetime import datetime
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration
from manage.utilities import msg_failure, message, failure, success


class Method(AbstractMethod):
    """Change the local README to update the version number (and date) for Unreleased changes."""

    args = Arguments(
        arguments=[
            Argument(
                name="readme",
                type_=str,
                default=None,
            ),
        ],
    )

    def __init__(self, configuration: Configuration, step: dict):
        """Update README."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        fails = []
        # Check to see if optional argument exists if provided
        if readme := self.get_arg("readme"):
            if not Path(readme).exists():
                fails.append(f"Sorry, path '[italic]{readme}[/]' could not be found for the {self.name} method.")

        # Check to see if we have one in the current directory
        cwd = Path.cwd()
        for format_ in ("org", "md"):
            readme_name = f"README.{format_}"
            path_readme = cwd / readme_name
            if path_readme.exists():
                break
        else:
            fails.append("Sorry, couldn't find either a README.org or " "README.md in the top-level directory!")

        return fails

    def run(self) -> bool:
        """Search for 'Unreleased...' header in Changelog portion of README and replace with current version and date.

        We essentially take the portion of the README that looks like this:
        ...
        * Release History
        ** Unreleased
           - changed this
           - changed that
        ** vA.B.C <older date>
        ...

        To this (for a patch release)
        ...
        * Release History
        ** Unreleased
        ** vA.B.D - <today>    <-- Adding this line based on configuration.version_ and today
           - changed this
           - changed that
        ** vA.B.C - <older date>
        ...
        """
        # Has the user provided an explicit path to the README file to work on?
        if not (path_readme := self._get_readme_path()):
            return False

        release_tag = f"{self.configuration.version} - {datetime.now().strftime('%Y-%m-%d')}"  # eg. vA.B.C - 2023-05-15

        ################################################################################
        # Read the changelog/release section embedded in our readme and update contents
        # with the new version (leaving another "Unreleased" header for future work).
        ################################################################################
        readme_contents = path_readme.read_text()

        # Since we don't know what particular heading level "Unreleased" is, we need to scan through
        # the contents to find out...
        unreleased_header = None
        for line in readme_contents.split("\n"):
            if "unreleased" in line.casefold():
                unreleased_header = line

        # Confirm that we actually *found* the "Unreleased" header (irrespective of format):
        if not unreleased_header:
            failure()
            msg_failure(f"Sorry, couldn't find a header-line with 'Unreleased' in {path_readme.name}!")
            return False

        # We want to place the new version header at the same level as the current 'Unreleased',
        # thus, we "build" the new release header line FROM the existing unreleased one, ensuring
        # we'll match header levels!
        new_release_header = unreleased_header.lower().replace("unreleased", release_tag)

        # Finally, we can replace the current unrelease_header line with the new contents..
        readme_contents = readme_contents.replace(unreleased_header, unreleased_header + "\n" + new_release_header)

        ################################################################################
        # Dry-run
        ################################################################################
        cmd = f"update {path_readme.name}'s '[italic]Unreleased[/]' header to '[italic]{release_tag}[/]'"
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        ################################################################################
        # Confirmation
        ################################################################################
        if not self.do_confirm(f"Ok to {cmd}?"):
            return False

        # RUN!!
        if self.step.verbose:
            message(f"Running update on {path_readme.name} version to: '{unreleased_header}'")

        path_readme.write_text(readme_contents)

        if self.step.verbose:
            success()

        return True

    def _get_readme_path(self) -> Path | None:
        """Get the default path we'll be working on?.

        Note: this is primarily for testing purposes, as manage
        is intended to be run from the project's top level directory!
        """
        if s_readme := self.get_arg("readme", optional=True):
            # Yes, make sure we can find it..
            return Path(s_readme)
        else:
            # Not specified, look for default README
            for format_ in ("org", "md"):
                path_readme = Path.cwd() / f"README.{format_}"
                if path_readme.exists():
                    return path_readme
        return None
