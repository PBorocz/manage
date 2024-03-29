"""Core data types."""
from argparse import Namespace
from typing import Self, TypeVar

from pydantic import BaseModel

from manage.utilities import msg_debug


TConfiguration = TypeVar("TConfiguration", bound="Configuration")
TPyProject = TypeVar("TPyProject")


class Configuration(BaseModel):
    """Configuration, read-only instance to keep command-line args and particular pyproject attributes."""

    # fmt: off
    # Commands to use once and then exit
    do_help     : bool | None = None  # Were we requested to just display help?
    do_print    : bool | None = None  # Were we requested to print the recipes contents?
    do_validate : bool | None = None  # Validate recipes and quit?

    # Standard execution arguments (including method specific ones)
    debug       : bool | None = None  # Are we running in debug mode?
    verbose     : bool | None = None  # Are we running in verbose mode?
    target      : str  | None = None  # What is the target to be performed?
    confirm     : bool | None = None  # Should we perform confirmations on steps?
    dry_run     : bool | None = None  # Are we running in dry-run mode (True) or live mode (False)
    method_args : list | None = []    # Set of "dynamic" arguments for specific methods (from CLI)
    # fmt: on

    @classmethod
    def get_version_fmt(cls, version_raw: str | None) -> str:
        """Get formatted version from a raw one."""
        return f"v{version_raw}" if version_raw else ""

    def find_method_arg_value(self, cls: str, arg: str) -> str | None:
        """Find/return the the command-line argument for the respective method/class and argument."""
        for (method, arg), value in self.method_args:
            if cls.casefold() == method and arg.casefold() == arg:
                return value
        return None

    @classmethod
    def factory(cls, args: tuple[Namespace, dict], test: bool = False, **kwargs_testing) -> Self:
        """Create a Configuration object instance from our args and user's pyproject.toml."""
        static_args, method_args = args

        conf_parms = {
            "method_args": method_args,
        }

        # Get the rest of the "standard" command-line parameters
        if static_args:
            for arg in vars(static_args):
                conf_parms[arg] = getattr(static_args, arg)

        # Finally, for testing only, override any other attrs:
        if kwargs_testing:
            for attr, value in kwargs_testing.items():
                conf_parms[attr] = value

                # Verbose output to be nice??
                if conf_parms.get("verbose") or test:
                    msg_debug(f"- (setting [italic]{attr}[/] to {value} from kwargs_testing")

        return Configuration(**conf_parms)
