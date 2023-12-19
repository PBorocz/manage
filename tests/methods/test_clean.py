"""."""
import pytest
import unittest.mock as mock
from pathlib import Path

from manage.models import Configuration, Recipes, Step
from manage.methods.clean import Method as clean  # noqa: N813


@pytest.fixture
def configuration():
    return Configuration(dry_run=False)


@pytest.fixture
def recipes():
    return Recipes.parse_obj({})


@pytest.fixture
def step_no_confirm():
    return Step(method="aMethod", confirm=False, verbose=False)


@pytest.fixture
def step_confirm():
    return Step(method="aMethod", confirm=True, verbose=True)


@pytest.fixture
def mock_input():
    with mock.patch("rich.console.input") as m:
        yield m


def test_clean_with_confirm(configuration, recipes, step_confirm, mock_input):
    mock_input.return_value = "y"
    assert clean(configuration, recipes, step_confirm).run()

    mock_input.return_value = "n"
    assert not clean(configuration, recipes, step_confirm).run()


def test_clean_no_confirm(configuration, recipes, step_no_confirm, mock_input):
    path_build = Path("build")

    # With an existing file, command should delete it!
    path_build.touch()
    assert path_build.exists()
    clean(configuration, recipes, step_no_confirm).run()
    assert not path_build.exists()
