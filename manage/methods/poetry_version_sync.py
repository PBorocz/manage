"""Change the local __version__.py file to reflect the version number from pyproject.toml."""
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration, PyProject
from manage.utilities import msg_failure, message, failure, success


class Method(AbstractMethod):
    """Change the local __version__.py file to reflect the version number from pyproject.toml."""

    args = Arguments(
        arguments=[
            Argument(
                name="init_path",
                type_=str,
                default=Path.cwd() / Path("__init__.py"),
            ),
        ],
    )

    def __init__(self, configuration: Configuration, step: dict):
        """Setup."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Perform any pre-method validation."""
        # Check to see if __init__.py file exists
        if init_file := self.get_arg("init_path"):
            if not Path(init_file).exists():
                msg = f"Sorry, path '[italic]{init_file}[/]' could not be found for the {self.name} method."
                return [msg]

    def run(self, **testing_kwargs) -> bool:
        """Search for line like '__version__ = <foo>' and replace foo with current version from pyproject.toml."""
        # We use the live version of the pyproject file (in case a previous step updated it since we started this run!)
        kwargs = {"debug": self.configuration.debug}
        if "path_pyproject" in testing_kwargs:  # Allow for testing override...
            kwargs["path_pyproject"] = testing_kwargs["path_pyproject"]
        pyproject: PyProject = PyProject.factory(**kwargs)

        # Setup the new "version" line we'll be putting into the __init__.py
        release_tag = f"{pyproject.version}"  # eg. A.B.C
        match_pattern = "__version__ ="
        new_version_line = f'{match_pattern} "{release_tag}"'

        # Read the current contents of __init__.py
        path_init_py = Path(self.get_arg("init_path"))
        init_contents = path_init_py.read_text()

        # Look for our "version" line..
        version_line = None
        for line in init_contents.split("\n"):
            if line.casefold().startswith(match_pattern):
                version_line = line
                old_version = line.replace(match_pattern, "").strip().replace('"', "")

        # Did we find it?
        if not version_line:
            failure()
            msg_failure(f"Sorry, couldn't find line starting with '[italic]{match_pattern}[/]' in {path_init_py.name}!")
            return False

        action = (
            f"update {path_init_py.name}'s [italic]__version__[/] line "
            f"from [italic]{old_version}[/] to [italic]{release_tag}[/]"
        )

        ################################################################################
        # Dry-run
        ################################################################################
        if self.configuration.dry_run:
            self.dry_run(action)
            return True

        ################################################################################
        # Confirmation
        ################################################################################
        if not self.do_confirm(f"Ok to {action}?"):
            return False

        # RUN!! Replace the current unrelease_header line with the new contents and write it out!
        if self.step.verbose:
            message(f"Running update on {path_init_py.name} __version__ to: '{new_version_line}'")

        init_contents = init_contents.replace(version_line, new_version_line)
        path_init_py.write_text(init_contents)

        if self.step.verbose:
            success()

        return True
