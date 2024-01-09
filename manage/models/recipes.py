"""Core data types."""
from rich.console import Console
from typing import Iterable, Self, TypeVar

from pydantic import RootModel

TClass = TypeVar("Class")
TRecipe = TypeVar("TRecipes")
TConfiguration = TypeVar("TConfiguration")
TPyProject = TypeVar("TRecipes")
TRecipes = TypeVar("TRecipes", bound="Recipes")


class Recipes(RootModel):
    """A collection of recipes, maps 1-to-1 with an inbound file."""

    root: dict[str, TRecipe] = {}

    def __len__(self):
        return len(self.root)

    def __iter__(self) -> Iterable[tuple[str, TRecipe]]:
        return iter(self.root.items())

    def get(self, id_: str) -> TRecipe | None:
        """Treat Recipes as a mapping, return a specific Recipe by it's id."""
        return self.root.get(id_)

    def set(self, id_: str, recipe: TRecipe) -> None:
        """Treat Recipes as a mapping, setting a specific Recipe using it's id."""
        self.root[id_] = recipe

    def keys(self) -> Iterable[str]:
        """Get the names of all Recipes."""
        return iter(sorted(self.root.keys()))

    def check_target(self, recipe_target: str) -> bool:
        """Is the target provide valid against our current recipes? (on a case-folded basis)."""
        return recipe_target.casefold() in [id_.casefold() for id_ in self.keys()]

    def print(self, configuration: TConfiguration):
        """Print either all the recipes or only that for target."""
        console = Console(width=60)
        for recipe_name, recipe in self:
            if configuration.target and configuration.target != recipe_name:
                continue
            recipe.print(console, recipe_name, configuration)
        return True

    def validate_all_recipes(self, configuration: TConfiguration, fails: list[str] = []) -> list[str]:
        """Validate all recipes defined (using method above to walk each one) and returning all issues encountered."""
        all_msgs = set()
        for recipe_id, recipe in self:
            if msgs := self.validate_recipe(configuration, recipe_id):
                all_msgs.update(msgs)
        return list(all_msgs)

    def validate_recipe(self, configuration: TConfiguration, target: str, fails: list[str] = []) -> list[str]:
        """Walk the tree and validate a *specific* recipe."""
        for step in self.get(target):
            # Each step to be performed could be either a method OR another step:
            if step.class_:
                # Instantiate the method's class associated with the step and validate it!
                if msgs := step.class_(configuration, step).validate():
                    fails.extend(msgs)
            else:
                # Run another recipe!
                self.validate_recipe(configuration, step.recipe, fails)
        return fails

    def run(self, configuration: TConfiguration):
        """Walk the tree, either calling 'run' on the respective method."""
        for step in self.get(configuration.target):
            # Each step to be performed could be either a method OR another step:
            if step.class_:
                # Instantiate the method's class associated with the step
                step.class_(configuration, step).run()
            else:
                # Run another recipe!
                configuration.target = step.recipe  # Override the target (but leave the rest)
                self.walk(configuration)

    @classmethod
    def factory(cls, configuration: TConfiguration, pyproject: TPyProject, method_classes: dict[str, TClass]) -> Self:
        """We want a clean/easy-to-use recipe file, thus, do our own deserialisation and embellishment."""
        from manage.models import Recipe

        d_recipes = dict(
            (recipe_name, Recipe.factory(configuration, method_classes, **raw_recipe))
            for recipe_name, raw_recipe in pyproject.recipes.items()
        )
        return cls.model_validate(d_recipes)
