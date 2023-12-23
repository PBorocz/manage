"""Test ability to convert raw_recipes into strongly-typed instances."""
import tomllib
from pathlib import Path

import pytest
from manage.models import Configuration, Step, PyProject, Recipe, Recipes


class Namespace:
    """Emulate arg result from argparse."""

    def __init__(self, *args, **kwargs):
        """Emulate arg result from argparse."""
        self.__dict__ = kwargs


@pytest.fixture
def recipes():
    # NOTE: Must match contents of tests/test_models.toml!
    recipe_clean = Recipe(
        description="A Clean Recipe",
        steps=[
            Step(
                method="clean",  # Test that defaults match those in toml file..
                confirm=True,
                verbose=False,
                allow_error=False,
                arguments=dict(arg_1_str="arg_1_str_value", arg_2_bool=False, arg_3_int=42),
            ),
            Step(method="print", confirm=True, verbose=True, allow_error=True),
        ],
    )

    recipe_build = Recipe(
        description="A Build Recipe",
        steps=[
            Step(recipe="clean"),
            Step(method="build"),
        ],
    )
    return Recipes.parse_obj(
        {
            "clean": recipe_clean,
            "build": recipe_build,
        },
    )


def test_recipe_factory(recipes):
    # Setup
    raw_pyproject = PyProject.factory(tomllib.loads(Path("tests/test_models.toml").read_text()))
    configuration = Configuration.factory(Namespace(), raw_pyproject, test=True)

    # Test
    recipes_from_file = Recipes.factory(configuration, raw_pyproject, {})

    # Confirm
    assert len(recipes) == len(recipes_from_file)
    assert sum([len(recipe) for recipe in recipes]) == sum([len(recipe) for recipe in recipes_from_file])
    for name in sorted(recipes.keys()):
        recipe = recipes.get(name)
        recipe_from_file = recipes_from_file.get(name)
        assert recipe == recipe_from_file


def test_parse_dynamic_arguments():
    # FIXME: Implement me..
    ...


def tst_validate_existing_version_numbers():
    # FIXME: Implement me..
    ...


def tst_validate_recipe_methods():
    # FIXME: Implement me..
    ...


def tst_add_callables():
    # FIXME: Implement me..
    ...


def tst_add_system_recipes():
    # FIXME: Implement me..
    ...


def tst_override_steps_from_args():
    # FIXME: Implement me..
    ...


def tst_gather_available_method_classes():
    # FIXME: Implement me..
    ...
