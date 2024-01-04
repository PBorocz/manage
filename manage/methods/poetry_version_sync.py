"""Change the local __version__.py file to reflect the version number from pyproject.toml."""
from pathlib import Path

from manage.methods import AbstractMethod
from manage.models import Argument, Arguments, Configuration
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

    def run(self) -> bool:
        """Search for line like '__version__ = <foo>' and replace foo with current version."""
        release_tag = f"{self.configuration.version_}"  # eg. A.B.C
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

        # Did we find it?
        if not version_line:
            failure()
            msg_failure(f"Sorry, couldn't find line starting with '[italic]{match_pattern}[/]' in {path_init_py.name}!")
            return False

        ################################################################################
        # Dry-run
        ################################################################################
        cmd = f"update {path_init_py.name}'s '[italic]{version_line}[/]' to '[italic]{new_version_line}[/]'"
        if self.configuration.dry_run:
            self.dry_run(cmd)
            return True

        ################################################################################
        # Confirmation
        ################################################################################
        if not self.do_confirm(f"Ok to {cmd}?"):
            return False

        # RUN!! Replace the current unrelease_header line with the new contents and write it out!
        if self.step.verbose:
            message(f"Running update on {path_init_py.name} __version__ to: '{new_version_line}'")

        init_contents = init_contents.replace(version_line, new_version_line)
        path_init_py.write_text(init_contents)

        if self.step.verbose:
            success()

        return True
