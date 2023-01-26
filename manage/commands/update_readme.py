from datetime import datetime
from pathlib import Path

from rich import print

from manage.models import Configuration
from manage.utilities import ask_confirm, fmt, failure, success

UNRELEASED_HEADER = "*** Unreleased"
PATH_README = Path.cwd() / "README.org"


def main(configuration: Configuration, step: dict) -> bool:
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
    ** vA.B.D - <today>    <-- Adding this line based on configuration._version and today
       - changed this
       - changed that
    ** vA.B.C - <older date>
    ...

    """
    if step.get("confirm", False):
        msg = f"Ok to update README.org's 'Unreleased' header to {configuration.version()}?"
        if not ask_confirm(msg):
            print("Nothing done (but pyproject.toml may still be on new version)")
            return False

    # Read and update the Changelog section embedded our README.org with the
    # new version (leaving another "Unreleased" header for future work)
    readme = PATH_README.read_text()
    if UNRELEASED_HEADER not in readme:
        failure()
        print(f"[red]Sorry, couldn't find a header consisting of '{UNRELEASED_HEADER}' in README.org!")
        return False

    msg = fmt("Running update to README.org: '{UNRELEASED_HEADER}'", color='blue')
    print(msg, flush=True, end="")
    release_header = f"\n*** {configuration.version()} - {datetime.now().strftime('%Y-%m-%d')}"
    readme = readme.replace(
        UNRELEASED_HEADER,
        UNRELEASED_HEADER + release_header)

    PATH_README.write_text(readme)

    success()
    return True
