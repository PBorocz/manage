from datetime import datetime
from pathlib import Path

from rich import print

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, fmt, failure, success


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
    # What's the default path we'll be working on? (note: this is primarily for testing purposes), manage is intended to be run
    # from the project's top level directory)
    cwd = Path(step.arguments.get('cwd', Path.cwd()))

    # What file format are we working on?
    format_ = step.arguments.get("readme_format", "md")  # Default README file format if not specified.

    # What does the "Unreleased" line look like based on the format?
    if format_ == "md":
        header = "###"
    elif format_ == "org":
        header = "***"
    else:
        print(f"[red]Sorry, we don't support readme_format {format_} yet, must be one of 'md' or 'org'!")
        return False

    unreleased_header = f"{header} Unreleased"

    # README file name and path..
    readme_name = f"README.{format_}"
    path_readme = cwd / readme_name

    if step.confirm:
        msg = f"Ok to update {readme_name}'s 'Unreleased' header to {configuration.version()}?"
        if not ask_confirm(msg):
            print("Nothing done (but pyproject.toml may still be on new version)")
            return False

    # Read and update the Changelog section embedded in our readme with the new version (leaving another "Unreleased" header for
    # future work)
    readme_contents = path_readme.read_text()
    if unreleased_header not in readme_contents:
        failure()
        print(f"[red]Sorry, couldn't find a header consisting of '{unreleased_header}' in {readme_name}!")
        return False

    msg = fmt(f"Running update to {readme_name}: '{unreleased_header}'", color='blue')
    print(msg, flush=True, end="")
    release_header = f"\n{header} {configuration.version()} - {datetime.now().strftime('%Y-%m-%d')}"
    readme_contents = readme_contents.replace(
        unreleased_header,
        unreleased_header + "\n" + release_header)

    path_readme.write_text(readme_contents)

    success()
    return True
