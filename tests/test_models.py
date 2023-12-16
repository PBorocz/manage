
import pydantic
import pytest

from manage.models import Step, Recipe, Recipes


@pytest.fixture
def recipes():
    # NOTE: Must match contents of tests/test_models.toml!
    recipe_clean = Recipe(
        description="A Clean Recipe",
        steps=[
            Step(method="clean"),  # Test that defaults match those in toml file..
            Step(method="print",
                 config=True,
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
    })


def test_step():
    """Test simple step model validation."""
    # Normal case, either is required:
    Step(recipe="bar")
    Step(method="foo")

    # However, ValidatorErrors when neither is provided or if both are provided:
    with pytest.raises(pydantic.ValidationError):
        Step()
    with pytest.raises(pydantic.ValidationError):
        Step(recipe="aStep", method="aMethod")


def test_step_args():
    """Test step model argument handling."""
    test_args = {
        "arg_1_str": "arg_1_str_value",
        "arg_2_bool": True,
        "arg_3_int": 42,
    }
    # Test
    step = Step(method="bar", arguments=test_args)

    # Confirm
    assert step.arguments == test_args
    assert step.get_arg("arg_1_str") == "arg_1_str_value"
    assert step.get_arg("arg_2_bool") is True
    assert step.get_arg("arg_3_int") == 42


def test_recipe():
    step = Step(method="build")
    recipe = Recipe(description="Another Description", steps=[step])
    assert len(recipe) == 1


def test_recipe_step_validation(recipes):
    # assert recipes.validate_step_actions({}) is not None
    methods = {
        "clean"   : lambda x: x,
        "print"   : lambda x: x,
        "build"   : lambda x: x,
        "another" : lambda x: x,
    }
    assert not recipes.validate_methods_steps(methods)
