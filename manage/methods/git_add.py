"""Method to perform a 'git add' (aka stage) command."""
from pathlib import Path

from git import Repo

from manage.models import Configuration, Recipes, Arguments, Argument
from manage.utilities import ask_confirm, failure, message, success

PATHSPEC_ALL = "."

# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(name="pathspec",
             type_=str,
             default=PATHSPEC_ALL),
])


def main(
    configuration: Configuration,
    recipes: Recipes,
    step: dict,
    repo: Repo | None = None) -> bool:
    """Do a 'git add' command, either with a specific wildcard or all (if no argument specified).

    Use either repo provided (testing usually) or that in the current directory (normal mode).
    """
    repo = Repo(Path.cwd()) if not repo else repo

    # Get arguments...
    if step.arguments and 'pathspec' in step.arguments:
        pathspec = step.arguments.get("pathspec")
    else:
        pathspec = args.get_argument("pathspec").default

    # Stage changing commmand...confirm execution..
    if step.confirm:
        confirm = "Ok to git add (stage) all files?" if pathspec == PATHSPEC_ALL else f"Ok to git add {pathspec}?"
        if not ask_confirm(confirm):
            return False

    # Do it..
    try:
        results = repo.index.add([pathspec])
        success()
        if not step.quiet_mode:
            for base_index_entry in results:
                message(f"git add {base_index_entry.path}", color="green", end_success=True)
        return True
    except OSError:
        failure()
        if not step.quiet_mode:
            message(f"Unable to `git add {pathspec=}`", color="red", end_failure=True)
        return False
