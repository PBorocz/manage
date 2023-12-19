from rich import print

from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes, Recipe
from manage.utilities import message


class Method(AbstractMethod):
    """Show/print the recipes."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Print!"""
        super().__init__(configuration, recipes, step)

    def run(self):
        """Override and use our local run method to print."""
        if self.configuration.verbose:  # Can't use step.verbose here as we haven't reflected runtime args yet!
            message(
                "The following recipes are currently defined:",
                color="green",
                end_success=True,
            )
        for id_, recipe in self.recipes:
            self._print_recipe(id_, self.recipes, recipe)
        return True

    def _print_recipe(self, id_: str, recipes: Recipes, recipe: Recipe, indent_level: int = 0) -> None:
        """Print a recipe."""
        indent = " " * indent_level
        print(f"\n{indent}[bold italic]{id_}[/] ≫ {recipe.description}")
        for step in recipe:
            step.reflect_runtime_arguments(self.configuration, verbose=False)
            print(step.as_print())
