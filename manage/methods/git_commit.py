"""General git commit."""
from datetime import datetime
from pathlib import Path

from git import Repo

from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import ask_confirm, failure, message, success

PATHSPEC_ALL = "."

# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(
        name="message",
        type_=str,
        default=f"Commit as of {datetime.now().isoformat()}",
    ),
])

def main(configuration: Configuration, recipes: Recipes, step: dict, repo: Repo | None = None) -> bool:
    """Commits all staged files.

    Use either repo provided (testing usually) or that in the current directory (normal mode).
    """
    repo = Repo(Path.cwd()) if not repo else repo

    # Get argument...
    if not (commit_message := step.get_arg("message")):
        commit_message = args.get_argument("message").default

    # State changing commmand...confirm execution..
    confirm = f"Ok to '[italic]git commit -m \"{commit_message}\"[/]'?"
    if step.confirm and not ask_confirm(confirm):
            return False

    # Do it..
    try:
        repo.index.commit(commit_message)
        commit = repo.head.commit
        for file_, diff in commit.stats.files.items():
            message(f"git commit -m {file_}", color="green", end_success=True)
        return True
    except OSError:
        if step.verbose:
            message(f"Unable to '[italic]git commit -m \"{message}\"[/]", color="red", end_failure=True)
        return False
