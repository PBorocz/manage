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
    if step.arguments and "message" in step.arguments:
        commit_message = step.arguments.get("message")
    else:
        commit_message = args.get_argument("message").default

    # State changing commmand...confirm execution..
    if step.confirm:
        confirm = f"Ok to `git commit -m '{commit_message}'?"
        if not ask_confirm(confirm):
            return False

    # Do it..
    try:
        results = repo.index.commit(commit_message)
        # FIXME: This is displaying ALL entries in the tree, not just the ones committed!!
        for blob in results.tree:
            message(f"git commit -m {blob.name}", color="green", end_success=True)
        return True
    except OSError:
        if not step.quiet_mode:
            message(f"Unable to `git commit -m {message}`", color="red", end_failure=True)
        return False
