"""Method to perform a 'git add' (aka stage) command."""
from pathlib import Path

from git import Repo
from rich.markup import escape

from manage.models import Configuration, Recipes, Arguments, Argument
from manage.utilities import ask_confirm, failure, message, success

PATHSPEC_ALL = "."

# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(
        name="pathspec",
        type_=str,
        default=PATHSPEC_ALL,
    ),
])


def main(configuration: Configuration, recipes: Recipes, step: dict, repo: Repo | None = None) -> bool:
    """Do a 'git add' command, either with a specific wildcard or all (if no argument specified).

    Use either repo provided (testing usually) or that in the current directory (normal mode).
    """
    repo = Repo(Path.cwd()) if not repo else repo

    # Get arguments...
    if s_pathspec := step.get_arg("pathspec"):
        pathspec = s_pathspec.split(" ")
        confirm = f"Ok to 'git add {','.join(pathspec)}'?"
    else:
        pathspec = [args.get_argument("pathspec").default]
        confirm = "Ok to 'git add *'?"

    # State changing commmand...confirm execution..
    if step.confirm and not ask_confirm(escape(confirm)):
        return False

    # Do it..
    try:
        results = repo.index.add(pathspec)
        if step.verbose:
            for base_index_entry in results:
                message(f"git add {base_index_entry.path}", color="green", end_success=True)
        return True
    except OSError:
        message(f"Unable to `git add {pathspec=}`", color="red", end_failure=True)
        return False
