"""Change the local README to update the version number (and date) for Unreleased changes."""
from datetime import datetime
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import message, failure, success

# Metadata about arguments available...
args = Arguments(
    arguments=[
        Argument(
            name="readme",
            type_=str,
            default=None,
        ),
        Argument(
            name="cwd",
            type_=str,
            default=Path.cwd(),
        ),
    ],
)


class Method(AbstractMethod):
    """Change the local README to update the version number (and date) for Unreleased changes."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Update README."""
        super().__init__(configuration, recipes, step)

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
        # What's the default path we'll be working on? (note: this is primarily for testing
        # purposes), manage is intended to be run from the project's top level directory!)
        cwd = Path(self.get_arg("cwd", optional=True, default=Path.cwd()))

        # Has the user provided an explicit path to the README file to work on?
        if s_readme := self.get_arg("readme", optional=True):
            # Yes, make sure we can find it..
            path_readme = Path(s_readme)
            if not path_readme.exists():
                failure()
                message(f"Sorry, couldn't find file with path '{path_readme}'!", color="red")
                return False
            readme_name = path_readme.name
        else:
            # Not specified, look for default README
            for format_ in ("org", "md"):
                readme_name = f"README.{format_}"
                path_readme = cwd / readme_name
                if path_readme.exists():
                    break
            else:
                failure()
                message(
                    "Sorry, couldn't find either a README.org or " "README.md in the top-level directory!",
                    color="red",
                )
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
            message(f"Sorry, couldn't find a header-line with 'Unreleased' in {readme_name}!", color="red")
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
        cmd = f"update {readme_name}'s '[italic]Unreleased[/]' header to '[italic]{release_tag}[/]'"
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        ################################################################################
        # Confirmation
        ################################################################################
        if not self.do_confirm(f"Ok to {cmd}?"):
            return False

        # RUN!!
        message(f"Running update to {readme_name}: '{unreleased_header}'")
        path_readme.write_text(readme_contents)
        success()
        return True
