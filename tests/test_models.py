import pydantic
import pytest
import yaml
from manage.models import Step, Recipe, Recipes


@pytest.fixture
def recipes():
    # NOTE: Must match contents of tests/test_models.toml!
    s1 = Step(action="clean_step_1")
    s2 = Step(action="clean_step_2", config=True, echo_stdout=True, allow_error=True, quiet_mode=True)
    r1 = Recipe(description="A Description", steps=[s1, s2])

    s3 = Step(action="build")
    r2 = Recipe(description="Another Description", steps=[s3,])

    return Recipes.parse_obj({
        "clean" : r1,
        "build" : r2,
    })


def test_step_validation(recipes):
    # Action is required...
    Step(action="foo")

    # however:
    with pytest.raises(pydantic.ValidationError):
        Step()


def test_recipe_step_validation(recipes):
    # assert recipes.validate_step_actions({}) is not None
    methods = {
        "clean_step_1" : lambda x: x,
        "clean_step_2" : lambda x: x,
        "build": lambda x: x,
        "another": lambda x: x,
    }
    assert not recipes.validate_step_actions(methods)
