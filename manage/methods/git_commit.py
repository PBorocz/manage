"""General git commit."""
from datetime import datetime
from pathlib import Path

from git import Repo

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import message

# Metadata about arguments available...
DEFAULT_ARGS = Arguments(
    arguments=[
        Argument(
            name="message",
            type_=str,
            default=f"Commit as of {datetime.now().isoformat()}",
        ),
    ],
)


class Method(AbstractMethod):
    """git commit."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Define git commit."""
        super().__init__(configuration, recipes, step)

    def run(self, repo: Repo | None = None) -> bool:
        """Commits *all* staged files (ie. normal git commit).

        Use either repo provided (testing usually) or that in the current directory (normal mode).
        """
        repo = Repo(Path.cwd()) if not repo else repo

        # Get argument...
        if not (commit_message := self.step.get_arg("message")):
            commit_message = DEFAULT_ARGS.get_argument("message").default

        cmd = f'git commit -m "{commit_message}"'

        # State changing commmand...if we're going to run live, confirm execution beforehand.
        confirm = f"Ok to '[italic]{cmd}[/]'?"
        if not self.do_confirm(confirm):
            return False

        # Do it?
        try:
            # Dry-run?
            if self.configuration.dry_run:
                self.dry_run(cmd)
                return True

            # Do it!
            repo.index.commit(commit_message)
            if self.step.verbose:
                commit = repo.head.commit
                for file_, diff in commit.stats.files.items():
                    message(f'git commit -m "{file_}"', color="green", end_success=True)
            return True

        except OSError:
            message(f"Unable to '[italic]{cmd}[/]'", color="red", end_failure=True)
            return False
