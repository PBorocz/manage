"""Test Step model."""
import pydantic
import pytest

from manage.models import Step


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
    test_args = dict(arg_1_str="arg_1_str_value", arg_2_bool=True, arg_3_int=42)

    # Test
    step = Step(method="bar", arguments=test_args)

    # Confirm
    assert step.arguments == test_args
    assert step.get_arg("arg_1_str") == "arg_1_str_value"
    assert step.get_arg("arg_2_bool") is True
    assert step.get_arg("arg_3_int") == 42
