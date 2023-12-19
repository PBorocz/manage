"""Method to perform a 'git add' (aka stage) command."""
from pathlib import Path

from git import Repo
from rich.markup import escape

from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes, Arguments, Argument
from manage.utilities import message, smart_join

# Metadata about arguments available...
DEFAULT_ARGS = Arguments(
    arguments=[
        Argument(
            name="pathspec",
            type_=str,
            default=".",
        ),
    ],
)


class Method(AbstractMethod):
    """git add."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Define git add."""
        super().__init__(configuration, recipes, step)

    def run(self, repo: Repo | None = None) -> bool:
        """Do a 'git add' command, either with a specific wildcard or all (if no argument specified).

        Use either repo provided (testing usually) or that in the current directory (normal mode).
        """
        ...
        repo = Repo(Path.cwd()) if not repo else repo

        # Get arguments (and matching confirm message)
        if s_pathspec := self.get_arg("pathspec", optional=True):
            pathspec = s_pathspec.split(" ")
            confirm = f"Ok to 'git add {','.join(pathspec)}'?"
        else:
            pathspec = [DEFAULT_ARGS.get_argument("pathspec").default]
            confirm = "Ok to 'git add *'?"

        if self.configuration.dry_run:
            self.dry_run(f"git add {smart_join(pathspec, delim='')}")
            return True

        # State changing commmand...confirm execution beforehand...
        if not self.do_confirm(escape(confirm)):
            return False

        # Do it!
        try:
            results = repo.index.add(pathspec)
            if self.step.verbose:
                for base_index_entry in results:
                    message(f"git add {base_index_entry.path}", color="green", end_success=True)
            return True

        except OSError:
            message(f"Unable to `git add {pathspec=}`", color="red", end_failure=True)
            return False
