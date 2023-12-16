"""Test ability to convert raw_recipes into strongly-typed instances."""
from pathlib import Path

import pytest
from manage.models import Step, Recipe, Recipes
from manage.setup import read_pyproject, uptype_recipes


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
            Step(method="clean",  # Test that defaults match those in toml file..
                 confirm=True,
                 verbose=False,
                 allow_error=False,
                 arguments=
                     dict(arg_1_str="arg_1_str_value",
                          arg_2_bool=False,
                          arg_3_int=42),
                 ),
            Step(method="print",
                 confirm=True,
                 verbose=True,
                 allow_error=True),
        ],
    )

    recipe_build = Recipe(
        description="A Build Recipe",
        steps=[
            Step(recipe="clean"),
            Step(method="build"),
        ],
    )
    return Recipes.parse_obj({
        "clean" : recipe_clean,
        "build" : recipe_build,
        "check" : Recipe(description="Check configuration only.", steps=[Step(method="check", confirm=False)]),
        "print" : Recipe(description="Show/print recipe file contents.", steps=[Step(method="print", confirm=False)]),
    })


def test_read_pyproject(recipes):
    args = Namespace(recipes=Path("tests/test_models.toml"), no_confirm=None)
    raw_pyproject = read_pyproject(False, args.recipes)
    assert raw_pyproject is not None
    assert isinstance(raw_pyproject, dict)
    assert len(raw_pyproject) == 1
    assert "tool" in raw_pyproject
    assert "manage" in raw_pyproject.get("tool")
    assert "recipes" in raw_pyproject.get("tool").get("manage")


def test_uptype_recipes(recipes):
    args = Namespace(recipes=Path("tests/test_models.toml"), no_confirm=None)
    raw_pyproject = read_pyproject(False, args.recipes)
    recipes_from_file = uptype_recipes(args, raw_pyproject, None)
    assert len(recipes) == len(recipes_from_file)
    assert sum([len(recipe) for recipe in recipes]) == sum([len(recipe) for recipe in recipes_from_file])
    assert recipes == recipes_from_file

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

def tst_gather_available_methods():
    # FIXME: Implement me..
    ...
