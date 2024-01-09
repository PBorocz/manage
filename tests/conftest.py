"""Conftest."""
import pytest

from manage.models import Recipe, Recipes, Step


@pytest.fixture
def recipes():
    # NOTE: Must match contents of tests/test_models.toml!
    recipe_clean = Recipe(
        description="A Clean Recipe",
        steps=[
            Step(
                method="clean",
                confirm=False,
                verbose=False,
                allow_error=False,
                arguments={
                    "arg_1_str": "arg_1_str_value",
                    "arg_2_bool": False,
                    "arg_3_int": 42,
                },
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

    return Recipes.model_validate(
        {
            "clean": recipe_clean,
            "build": recipe_build,
        },
    )
