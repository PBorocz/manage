"""Core data types."""
from rich.console import Console
from typing import Iterable, Self, TypeVar

from pydantic import BaseModel


TClass = TypeVar("Class")
TRecipe = TypeVar("TRecipes")
TConfiguration = TypeVar("TConfiguration")
TPyProject = TypeVar("TRecipes")
TRecipes = TypeVar("TRecipes", bound="Recipes")


class Recipes(BaseModel):
    """A collection of recipes, maps 1-to-1 with an inbound file."""

    __root__: dict[str, TRecipe] = {}

    def __len__(self):
        return len(self.__root__)

    def __iter__(self) -> Iterable[tuple[str, TRecipe]]:
        return iter(self.__root__.items())

    def get(self, id_: str) -> TRecipe | None:
        """Treat Recipes as a mapping, return a specific Recipe by it's id."""
        return self.__root__.get(id_.casefold())

    def set(self, id_: str, recipe: TRecipe) -> None:
        """Treat Recipes as a mapping, setting a specific Recipe using it's id."""
        self.__root__[id_] = recipe

    def keys(self) -> Iterable[str]:
        """Get the names of all Recipes."""
        return iter(sorted(self.__root__.keys()))

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

    def walk(self, configuration: TConfiguration, validate: bool = False):
        """Walk the tree, either calling the 'run' or 'validate' method on the respective method."""
        for step in self.get(configuration.target):
            # Each step to be performed could be either a method OR another step:
            if step.class_:
                # Instantiate the method's class associated with the step
                instance = step.class_(configuration, step)

                # Either validate the step or run for realsies..
                if validate:
                    instance.validate()
                else:
                    instance.run()
            else:
                # Run another recipe!
                configuration.target = step.recipe  # Override the target (but leave the rest)
                self.walk(configuration, validate)

    @classmethod
    def factory(cls, configuration: TConfiguration, pyproject: TPyProject, method_classes: dict[str, TClass]) -> Self:
        """We want a clean/easy-to-use recipe file, thus, do our own deserialisation and embellishment."""
        from manage.models import Recipe

        d_recipes = dict(
            (recipe_name, Recipe.factory(configuration, method_classes, **raw_recipe))
            for recipe_name, raw_recipe in pyproject.recipes.items()
        )
        return cls.parse_obj(d_recipes)
