"""Core data types."""
from copy import deepcopy

from typing import Any, Dict, Self, TypeVar

from pydantic import BaseModel, validator

from manage.utilities import msg_debug

TClass = TypeVar("Class")
TConfiguration = TypeVar("TConfiguration")


class Step(BaseModel):
    """A step in a recipe."""

    # FROM inbound manage file:
    # fmt: off
    method      : str  | None = None  # Reference to the built-in method to run
    recipe      : str  | None = None  # Reference to the id_ of another recipe.

    confirm     : bool | None = None
    verbose     : bool | None = None
    allow_error : bool | None = None

    arguments   : Dict[str, Any] = {}  # Supplemental arguments for the callable

    # NOT from inbound manage file:
    class_: TClass | None = None  # Python method we'll instantiate and call if this is a "method" step.
    # fmt: off

    @validator("recipe", always=True)
    @classmethod
    def check_consistency(cls, v, field, values):
        """Ensure that EITHER method or another recipe is specified on creation.

        NOTE: We use ~recipe~ here as it's *after* the ~method~ attribute in field definition order!
        """
        if v is None and values["method"] is None:
            raise ValueError("must provide either method or recipe")
        if v is not None and values["method"] is not None:
            raise ValueError("must not provide both method and recipe")
        return v

    def get_arg(self, arg_key: str, default: Any | None = None) -> Any | None:
        """Return the value associated with the specified argument (or None)."""
        return self.arguments.get(arg_key, default)

    def name(self) -> str:
        """Return a description name for this step, i.e. either method or recipe."""
        if self.method:
            return self.method
        return self.recipe

    def __reflect_runtime_arguments(self, configuration: TConfiguration) -> Self:
        """Update the step based on any/all arguments received on the command-line."""
        # Two STATIC command-line args can trickle down to individual step execution: 'confirm' and 'verbose':
        if configuration.confirm is not None and self.confirm != configuration.confirm:
            if configuration.debug:
                msg = (
                    f"- {self.name()}: overriding [italic]confirm[/] from "
                    f"[italic]{self.confirm}[/] to [italic]{configuration.confirm}[/]"
                )
                msg_debug(msg)
            self.confirm = configuration.confirm

        if configuration.verbose is not None and self.verbose != configuration.verbose:
            if configuration.debug:
                msg = (
                    f"- {self.name()}: overriding [italic]verbose[/] from "
                    f"[italic]{self.verbose}[/] to [italic]{configuration.debug}[/]"
                )
                msg_debug(msg)
            self.verbose = configuration.verbose

        # However, we might have any number of DYNAMIC command-line args *specific* to this method:
        if self.method:  # Only true if this step is a method, e.g. git_commit
            for (method_name, method_arg), cli_value in configuration.method_args:  # e.g. ("git_commit","message"),".."
                if method_name.casefold() == self.method.casefold():
                    if method_arg in self.arguments:
                        if configuration.debug:
                            msg = (
                                f"- {self.name()}: overriding [italic]{method_arg}[/] from "
                                f"[italic]{self.arguments[method_arg]}[/] to [italic]{cli_value}[/]"
                            )
                            msg_debug(msg)
                        self.arguments[method_arg] = cli_value

        return self

    @classmethod
    def factory(cls, configuration: TConfiguration, method_classes: dict[str, TClass], **step_args) -> Self:
        """Return a new Step instance based on args and current configuration."""
        step = cls(**step_args)

        # Add the instantiable class onto each method step to dispatch from:
        step.class_ = method_classes.get(step.method, None)

        # Ripple command-line argument overrides to each step:
        step.__reflect_runtime_arguments(configuration)

        return step

    def _str_(self) -> dict:
        """Return a 'cleaned-up' copy of this step for printing."""
        step = deepcopy(self)

        # We don't need this for printing..
        delattr(step, "class_")

        if step.confirm is None:
            delattr(step, "confirm")

        # And one of these will be empty!
        if step.method:
            delattr(step, "recipe")
        else:
            delattr(step, "method")

        return step.__dict__
