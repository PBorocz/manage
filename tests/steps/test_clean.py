import pytest
import unittest.mock as mock
from pathlib import Path

from manage.models import Configuration, Recipes, Step
from manage.steps.clean import main as clean


@pytest.fixture
def configuration():
    return Configuration()


@pytest.fixture
def recipes():
    return Recipes.parse_obj({})


@pytest.fixture
def step_no_confirm():
    return Step(method="aMethod", confirm=False, quiet_mode=True)


@pytest.fixture
def step_confirm():
    return Step(method="aMethod", confirm=True, quiet_mode=False)


@pytest.fixture
def mock_input():
    with mock.patch('rich.console.input') as m:
        yield m


def test_clean_with_confirm(configuration, recipes, step_confirm, mock_input):
    mock_input.return_value = 'y'
    assert clean(configuration, recipes, step_confirm)

    mock_input.return_value = 'n'
    assert not clean(configuration, recipes, step_confirm)


def test_clean_no_confirm(configuration, recipes, step_no_confirm, mock_input):
    path_build = Path('build')

    # With nothing, should work as is..
    assert clean(configuration, recipes, step_no_confirm)

    # With an existing file, should delete it.
    path_build.touch()
    assert path_build.exists()
    clean(configuration, recipes, step_no_confirm)
    assert not path_build.exists()
