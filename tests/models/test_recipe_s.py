"""Test Recipe/Recipes models."""
from pathlib import Path

from manage.models import Recipe, Step, PyProject, Configuration, Recipes


class Namespace:
    """Emulate arg result from argparse."""

    def __init__(self, *args, **kwargs):
        """Emulate arg result from argparse."""
        self.__dict__ = kwargs


def test_recipe_factory(recipes):
    # Setup
    raw_pyproject = PyProject.factory(Path("tests/models/test_models.toml"))
    configuration = Configuration.factory([Namespace(), []], test=True)

    # Test
    recipes_from_file = Recipes.factory(configuration, raw_pyproject, {})

    # Confirm
    assert len(recipes) == len(recipes_from_file)
    assert sum([len(recipe) for recipe in recipes]) == sum([len(recipe) for recipe in recipes_from_file])
    for name in sorted(recipes.keys()):
        recipe = recipes.get(name)
        recipe_from_file = recipes_from_file.get(name)
        assert recipe == recipe_from_file


def test_recipe():
    step = Step(method="build")
    recipe = Recipe(description="Another Description", steps=[step])
    assert len(recipe) == 1
