import pytest
import unittest.mock as mock
from pathlib import Path

from manage.models import Configuration, Step
from manage.steps.clean import main as clean


@pytest.fixture
def configuration():
    return Configuration()


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


def tst_clean_with_confirm(configuration, step_confirm, mock_input):
    mock_input.return_value = 'y'
    assert clean(configuration, step_confirm)

    mock_input.return_value = 'n'
    assert not clean(configuration, step_confirm)


def test_clean_no_confirm(configuration, step_no_confirm, mock_input):
    path_build = Path('build')

    # With nothing, should work as is..
    assert clean(configuration, step_no_confirm)

    # With an existing file, should delete it.
    path_build.touch()
    assert path_build.exists()
    clean(configuration, step_no_confirm)
    assert not path_build.exists()
