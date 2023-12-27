"""Core data types."""
from rich.console import Console
from typing import Self, TypeVar

from pydantic import BaseModel


TClass = TypeVar("Class")
TConfiguration = TypeVar("TConfiguration")
TStep = TypeVar("TStep")


class Recipe(BaseModel):
    """A recipe, consisting of a description and a set of steps."""

    description: str | None = None
    steps: list[TStep] = []

    def __iter__(self):
        return iter(self.steps)

    def __len__(self):
        return len(self.steps)

    def print(self, console: Console, name: str, configuration: TConfiguration) -> None:
        """Print the recipe to the specified console."""
        console.print(f"\n[bold italic]{name}[/] ≫ {self.description}")
        steps = [step._str_() for step in self.steps]
        console.print(steps)

    @classmethod
    def factory(cls, configuration: TConfiguration, method_classes: dict[str, TClass], **recipe_args) -> Self:
        """Return a new Recipe instance based on args and current configuration."""
        from manage.models import Step

        recipe = cls(description=recipe_args.get("description", "-"))
        recipe.steps = [Step.factory(configuration, method_classes, **d_step) for d_step in recipe_args.get("steps")]
        return recipe
