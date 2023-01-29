import pydantic
import pytest

from manage.models import Step, Recipe, Recipes


@pytest.fixture
def recipes():
    # NOTE: Must match contents of tests/test_models.yaml!
    recipe_clean = Recipe(
        description="A Clean Recipe",
        steps=[
            Step(method="clean"),  # Test that defaults match those in yaml file..
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
            Step(step="clean"),
            Step(method="build"),
        ]
    )
    return Recipes.parse_obj({
        "clean" : recipe_clean,
        "build" : recipe_build,
    })


def test_step():
    """Test simple step model validation"""

    # Normal case, either is required:
    Step(step="bar")
    Step(method="foo")
    with pytest.raises(pydantic.ValidationError):
        Step()
    with pytest.raises(pydantic.ValidationError):
        Step(step="aStep", method="aMethod")


def test_recipe():
    step = Step(method="build")
    recipe = Recipe(description="Another Description", steps=[step])
    assert len(recipe) == 1


def test_recipe_step_validation(recipes):
    # assert recipes.validate_step_actions({}) is not None
    methods = {
        "clean" : lambda x: x,
        "show" : lambda x: x,
        "build": lambda x: x,
        "another": lambda x: x,
    }
    assert not recipes.validate_methods_steps(methods)
