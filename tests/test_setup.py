from pathlib import Path

import pytest
from manage.models import Step, Recipe, Recipes
from manage.setup import _read_parse_recipe_file, _add_system_recipe_s


@pytest.fixture
def recipes():
    r1 = Recipe(name="Do Clean",
                description="A Description",
                steps=[
                    Step(action="clean_step_1"),
                    Step(action="clean_step_2", config=True, echo_stdout=True, allow_error=True, quiet_mode=True),
                ])
    r2 = Recipe(name="Do Build",
                description="Another Description",
                steps=[
                    Step(action="build"),
                ])

    return Recipes.parse_obj({
        "Do Clean" : r1,
        "Do Build" : r2,
    })


def test_read_parse_recipe_file(recipes):
    recipes_from_file = _read_parse_recipe_file(Path("tests/test_models.toml"))
    assert len(recipes) == len(recipes_from_file)
    assert sum([len(recipe) for recipe in recipes]) == sum([len(recipe) for recipe in recipes_from_file])
    assert recipes == recipes_from_file


def test_add_system_recipe_s(recipes):
    assert len(recipes) == 2
    recipes = _add_system_recipe_s(recipes)
    assert len(recipes) == 3
    assert recipes.get('check') is not None
