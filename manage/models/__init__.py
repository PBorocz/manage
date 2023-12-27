"""Core data types (with flattened namespace)."""

from typing import Any

from pydantic import BaseModel

# fmt: off
from .recipe        import Recipe        # noqa: F401
from .recipes       import Recipes       # noqa: F401
from .step          import Step          # noqa: F401
from .configuration import Configuration # noqa: F401
from .pyproject     import PyProject     # noqa: F401
# fmt: on


# These two are too small to warrant their own file:
class Argument(BaseModel):
    """Possible argument for a step method."""

    name: str
    type_: type
    default: Any | None = None


class Arguments(BaseModel):
    """Collection of Arguments for a step method."""

    arguments: list[Argument] = []

    def __iter__(self):
        for arg in self.arguments:
            yield arg

    def get_argument(self, argument_name: str) -> Argument | None:
        """Lookup Argument by name."""
        for arg in self.arguments:
            if arg.name == argument_name:
                return arg
        return None
