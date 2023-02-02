from pathlib import Path

import pytest
from manage.models import Step, Recipe, Recipes
from manage.setup import read_parse_recipe_file


@pytest.fixture
def recipes():
    # NOTE: Must match contents of tests/test_models.yaml!
    recipe_clean = Recipe(
        description="A Clean Recipe",
        steps=[
            Step(method="clean",  # Test that defaults match those in yaml file..
                 arguments=
                     dict(arg_1_str="arg_1_str_value",
                          arg_2_bool=False,
                          arg_3_int=42),
                 ),
            Step(method="show",
                 config=True,
                 echo_stdout=True,
                 allow_error=True,
                 quiet_mode=True),
        ]
    )

    recipe_build = Recipe(
        description="A Build Recipe",
        steps=[
            Step(recipe="clean"),
            Step(method="build"),
        ]
    )
    return Recipes.parse_obj({
        "clean" : recipe_clean,
        "build" : recipe_build,
        "check" : Recipe(description="Check configuration only.", steps=[Step(method="check")]),
        "show"  : Recipe(description="Show recipe file contents.", steps=[Step(method="show")]),
    })


def test_read_parse_recipe_file(recipes):
    recipes_from_file = read_parse_recipe_file(Path("tests/test_models.yaml"), None)
    assert len(recipes) == len(recipes_from_file)
    assert sum([len(recipe) for recipe in recipes]) == sum([len(recipe) for recipe in recipes_from_file])
    assert recipes == recipes_from_file
