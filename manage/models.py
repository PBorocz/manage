"""Core Data Types"""
from dataclasses import dataclass


@dataclass
class Configuration:
    _version: str = None
    package: str = None

    def version(self):
        """Return version number in "formal" format, usable (for instance) as git tag."""
        return f"v{self._version}"
