"""Change the local README.org to update the version number (and date) for Unreleased changes."""
from datetime import datetime
from pathlib import Path

from rich import print

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, message, failure, success


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
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
    cwd = Path(step.arguments.get('cwd', Path.cwd()))

    # Has the user provided an explicit path to the README file to work on?
    if s_readme := step.arguments.get("readme"):
        # Yes, make sure we can find it..
        path_readme = Path(s_readme)
        if not path_readme.exists():
            failure()
            print(f"[red]Sorry, couldn't find file with path '{path_readme}'!")
            return False

        readme_name = path_readme.name
    else:
        # Not specified, look for default of README.org or README.md
        for format_ in ("org", "md"):
            readme_name = f"README.{format_}"
            path_readme = cwd / readme_name
            if path_readme.exists():
                break
        else:
            failure()
            print("[red]Sorry, couldn't find either a README.org or README.md in the top-level directory!")
            return False

    release_tag = f"{configuration.version()} - {datetime.now().strftime('%Y-%m-%d')}" # eg. "vA.B.C - 2023-05-15"

    # Confirmation before we continue?
    if step.confirm:
        msg = f"Ok to update {readme_name}'s 'Unreleased' header to {release_tag}?"
        if not ask_confirm(msg):
            print("Nothing done")
            return False

    # Read and update the changelog/release section embedded in our readme with the new version
    # (leaving another "Unreleased" header for future work)
    readme_contents = path_readme.read_text()
    if "unreleased" not in readme_contents.lower():
        failure()
        print(f"[red]Sorry, couldn't find a header-line with 'Unreleased' in {readme_name}!")
        return False

    # Since we don't know what particular heading level "Unreleased" is, we need to scan through
    # the contents to find out...
    for line in readme_contents.split("\n"):
        if "unreleased" in line.lower():
            unreleased_header = line

    message(f"Running update to {readme_name}: '{unreleased_header}'")

    # We want to place the new version header at the same level as the current 'Unreleased',
    # thus, we "build" the new release header line FROM the existing unreleased one, ensuring
    # we'll match header levels!
    new_release_header = unreleased_header.lower().replace("unreleased", release_tag)

    # Finally, we can replace the current unrelease_header line with the new contents..
    readme_contents = readme_contents.replace(
        unreleased_header,
        unreleased_header + "\n" + new_release_header)

    # Save our file back out and we're done!
    path_readme.write_text(readme_contents)

    success()
    return True
