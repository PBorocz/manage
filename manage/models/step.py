"""Core data types."""
from copy import deepcopy
from typing import Any, Dict, Self, TypeVar

from pydantic import BaseModel, model_validator

from manage.utilities import msg_debug

TClass = TypeVar("Class")
TConfiguration = TypeVar("TConfiguration")


class Step(BaseModel):
    """A step in a recipe."""

    # fmt: off

    # FROM inbound manage file:
    method      : str  | None = None   # Reference to the built-in method to run
    recipe      : str  | None = None   # Reference to the id_ of another recipe.
    confirm     : bool | None = None
    verbose     : bool | None = None
    debug       : bool | None = None
    allow_error : bool | None = None
    arguments   : Dict[str, Any] = {}  # Supplemental arguments for the callable

    # NOT from inbound manage file:
    class_: TClass | None = None       # Python method we'll instantiate and call for a "method" step.

    # fmt: on

    @model_validator(mode="after")
    def check_consistency(self):
        """Ensure that EITHER method or another recipe is specified on creation."""
        if self.method is None and self.recipe is None:
            raise ValueError("must provide either method or recipe")
        if self.method and self.recipe:
            raise ValueError("must not provide both method and recipe")
        return self

    def get_arg(self, arg_key: str, default: Any | None = None) -> Any | None:
        """Return the value associated with the specified argument (or None)."""
        return self.arguments.get(arg_key, default)

    def name(self) -> str:
        """Return a description name for this step, i.e. either method or recipe."""
        if self.method:
            return self.method
        return self.recipe

    @classmethod
    def factory(cls, configuration: TConfiguration, method_classes: dict[str, TClass], **step_args) -> Self:
        """Return a new Step instance based on args and current configuration."""
        step = cls(**step_args)

        # Add the instantiable class onto each method step to dispatch from:
        step.class_ = method_classes.get(step.method, None)

        # Ripple command-line argument overrides to each step:
        step._reflect_runtime_arguments(configuration)

        return step

    def __reflect_variable(self, configuration: TConfiguration, var: str) -> None:
        msgs = []
        self_value = getattr(self, var)  # Current value of the attribute from the recipe file.
        conf_value = getattr(configuration, var)  # Potential override value of the attribute from the CLI.

        # Shortcut..
        if conf_value is None:
            return []

        if self_value is None:
            setattr(self, var, conf_value)
            msg = f"- {self.name():30s}: setting [italic]{var}[/] to [italic]{conf_value}[/]"
            msgs.append(msg)

        elif self_value != conf_value:
            setattr(self, var, conf_value)
            msg = (
                f"- {self.name():30s}: overriding [italic]{var}[/] from "
                f"[italic]{self_value}[/] to [italic]{conf_value}[/]"
            )
            msgs.append(msg)

        return msgs

    def _reflect_runtime_arguments(self, configuration: TConfiguration) -> Self:
        """Update the step based on any/all arguments received on the command-line."""
        debugs = []

        # Some command-line args can trickle down to individual step execution, do those here:
        debugs.extend(self.__reflect_variable(configuration, "debug"))
        debugs.extend(self.__reflect_variable(configuration, "verbose"))
        debugs.extend(self.__reflect_variable(configuration, "confirm"))

        # However, we might have any number of DYNAMIC command-line args *specific* to this method:
        if not self.method:  # Only true if this step is a method, e.g. git_commit
            return self
        for (method_name, method_arg), cli_value in configuration.method_args:  # e.g. ("git_commit","message"),".."
            if method_name == self.method:
                if default_arg := self.class_.args.get_argument(method_arg):
                    if default_arg.default:
                        debugs.append(
                            f"- {self.name()}: overriding [italic]{method_arg}[/] from "
                            f"[italic]{default_arg.default}[/] to [italic]{cli_value}[/] "
                            "from command-line",
                        )
                    else:
                        debugs.append(
                            f"- {self.name()}: setting [italic]{method_arg}[/] to [italic]{cli_value}[/] "
                            "from command-line",
                        )
                    self.arguments[method_arg] = cli_value

        if configuration.debug:
            for debug in debugs:
                msg_debug(debug)

        return self

    def _str_(self) -> dict:
        """Return a 'cleaned-up' copy of this step's __dict__ for printing."""
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
