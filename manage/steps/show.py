import rich

from manage.models import Configuration, Recipes


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Show the recipes."""
    rich.print(recipes)
    return True
