from rich import print

from manage.models import Configuration, Recipes, Recipe, Step
from manage.utilities import message


def main(configuration: Configuration, recipes: Recipes, step: dict = None) -> bool:
    """Show/print the recipes."""
    if step.verbose:
        message(
            f"The following recipes are currently defined in [italic]{configuration.recipes}[/]:",
            color="green",
            end_success=True,
        )
    for id_, recipe in recipes:
        print_recipe(configuration, id_, recipes, recipe)
    return True


def print_recipe(configuration: Configuration, id_: str, recipes: Recipes, recipe: Recipe, indent_level: int = 0) -> None:
    """Print a recipe."""
    indent = " " * indent_level
    print(f"\n{indent}[bold italic]{id_}[/] ≫ {recipe.description}")
    for step in recipe:
        step.reflect_runtime_arguments(configuration, verbose=False)
        print(step.as_print())
