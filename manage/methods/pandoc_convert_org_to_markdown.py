"""Convert an emacs org file into a markdown version using Pandoc."""
from rich import print

from manage.models import Argument, Arguments, Configuration
from manage.utilities import ask_confirm, message, run


# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(
        name="path_org",
        type_=str,
        default=None,
    ),
    Argument(
        name="path_md",
        type_=str,
        default=None,
    ),
])


def main(configuration: Configuration, _, step: dict) -> bool:
    """Do step."""
    if not (path_md := step.get_arg('path_md')):
        message("Sorry, command requires a supplemental argument for 'path_md'", color="red", end_failure=True)
        return False

    if not (path_org := step.get_arg('path_org')):
        message("Sorry, command requires a supplemental argument for 'path_org'", color="red", end_failure=True)
        return False

    cmd = f"pandoc -f org -t markdown --wrap none --output {path_md} {path_org}"
    confirm = f"Ok to run '[italic]{cmd}[/]'?"

    if step.confirm and not ask_confirm(confirm):
        return False

    try:
        return run(step, cmd)[0]
    except FileNotFoundError:
        print("\n[red]Sorry, couldn't find a [italic]pandoc[/] executable on your path!")
        return False
