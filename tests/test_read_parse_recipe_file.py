from pathlib import Path

import pytest
from manage.models import Step, Recipe, Recipes
from manage.setup import read_parse_recipe_file


@pytest.fixture
def recipes():

    # Test recipes:
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
        "clean" : r1,
        "build" : r2,

        # System recipes auto-added by read_parse_recipe_file:
        "check" : Recipe(description="Check configuration only", steps=[Step(action="check")]),
        "print" : Recipe(description="Print recipe file"),
    })


def test_read_parse_recipe_file(recipes):
    recipes_from_file = read_parse_recipe_file(Path("tests/test_models.yaml"), None)
    assert len(recipes) == len(recipes_from_file)
    assert sum([len(recipe) for recipe in recipes]) == sum([len(recipe) for recipe in recipes_from_file])
    assert recipes == recipes_from_file
