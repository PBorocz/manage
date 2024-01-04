"""Core data types."""
from argparse import Namespace
from typing import Self, TypeVar

from pydantic import BaseModel

from manage.utilities import msg_debug


TConfiguration = TypeVar("TConfiguration", bound="Configuration")
TPyProject = TypeVar("TPyProject")


class Configuration(BaseModel):
    """Configuration, primarily associated with command-line args to filter through step execution."""

    # fmt: off
    help        : bool | None = None  # Were we requested to just display help?
    print       : bool | None = None  # Were we requested to print the recipes contents?

    debug       : bool | None = None  # Are we running in debug mode?
    verbose     : bool | None = None  # Are we running in verbose mode?
    target      : str  | None = None  # What is the target to be performed?
    confirm     : bool | None = None  # Should we perform confirmations on steps?
    dry_run     : bool | None = None  # Are we running in dry-run mode (True) or live mode (False)
    method_args : list | None = []    # Set of "dynamic" arguments for specific methods (from CLI)

    version_    : str  | None = None  # Note: This is the current version # of the project we're working on!
    version     : str  | None = None  # " In nice format..
    package_    : str  | None = None  # "
    _messages_  : list[str] = []
    # fmt: on

    def set_value(self, attr: str, value: any, source: str) -> None:
        """Set the specified attr to the value given with verbosity."""
        setattr(self, attr, value)
        self._messages_.append(f"- (setting [italic]{attr}[/] to {value} {source})")

    def set_version(self, version_raw: str | None) -> None:
        """Set both the version attributes based on that provided from poetry."""
        version_formatted = f"v{version_raw}" if version_raw else ""
        self.version_ = version_raw
        self.version = version_formatted

    def find_method_arg_value(self, cls: str, arg: str) -> str | None:
        """Find/return the the command-line argument for the respective method/class and argument."""
        for (method, arg), value in self.method_args:
            if cls.casefold() == method and arg.casefold() == arg:
                return value
        return None

    @classmethod
    def factory(cls, args: tuple[Namespace, dict], pyproject: TPyProject, test: bool = False, **kwargs) -> Self:
        """Create a Configuration object instance from our args and user's pyproject.toml."""
        static_args, method_args = args

        ############################################################
        # CREATE our Configuration instance with these values
        ############################################################
        configuration = Configuration(package_=getattr(pyproject, "", ""), method_args=method_args)
        configuration.set_version(getattr(pyproject, "version", ""))

        # Get the rest of the known command-line parameters (whose
        # default values could have come from pyproject.toml!)
        for attr in ["confirm", "verbose", "help", "target", "dry_run", "print", "debug"]:
            if hasattr(static_args, attr):
                setattr(configuration, attr, getattr(static_args, attr))

        # Finally, for testing only, override any other attrs:
        if kwargs:
            for attr, value in kwargs.items():
                configuration.set_value(attr, value, "from (testing) kwargs")

        ############################################################
        # Verbose output to be nice??
        ############################################################
        for msg in configuration._messages_:
            if configuration.verbose or test:
                msg_debug(msg)

        return configuration
