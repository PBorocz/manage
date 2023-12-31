"""General git commit."""
import shutil
from datetime import datetime
from pathlib import Path

from git import Repo

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration
from manage.utilities import msg_failure, msg_success


class Method(AbstractMethod):
    """git commit."""

    args = Arguments(
        arguments=[
            Argument(
                name="message",
                type_=str,
                default=f"Commit as of {datetime.now().isoformat()}",
            ),
        ],
    )

    def __init__(self, configuration: Configuration, step: dict):
        """Define git commit."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> None:
        """Perform any pre-method validation."""
        # Check to see if executable is available
        exec_ = "git"
        if not shutil.which(exec_):
            msg = f"Sorry, Couldn't find '[italic]{exec_}[/]' is your path for the {self.name} method."
            self.exit_with_fails([msg])

    def run(self, repo: Repo | None = None) -> bool:
        """Commits *all* staged files (ie. normal git commit).

        Use either repo provided (testing usually) or that in the current directory (normal mode).
        """
        repo = Repo(Path.cwd()) if not repo else repo

        # Get argument...
        if not (commit_message := self.step.get_arg("message")):
            commit_message = Method.args.get_argument("message").default

        # Get the git commit command we'd like to run:
        cmd = f'git commit -m "{commit_message}"'

        # Dry-run?
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        # State changing commmand...if we're going to run live, confirm execution beforehand.
        confirm = f"Ok to '[italic]{cmd}[/]'?"
        if not self.do_confirm(confirm):
            return False

        # Do it!
        try:
            repo.index.commit(commit_message)
            if self.step.verbose:
                commit = repo.head.commit
                for file_, diff in commit.stats.files.items():
                    msg_success(f'git commit -m "{file_}"')
            return True
        except OSError:
            msg_failure(f"Unable to '[italic]{cmd}[/]'")
            return False
