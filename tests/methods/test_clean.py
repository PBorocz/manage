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
    return Recipes.model_validate({})


@pytest.fixture
def mock_input():
    with mock.patch("rich.console.input") as m:
        yield m


@pytest.fixture
def build_file():
    path_build = Path("build")
    path_build.touch()
    yield path_build
    # Cleanup..
    try:
        path_build.unlink()
    except FileNotFoundError:
        pass  # Ok some of the clean commands should WORK!


def test_clean(configuration, recipes, mock_input, capsys, build_file):
    """Test clean with an actual file (ie. actual functionality)."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False)

    # Test
    clean(configuration, step).run()

    # Confirm: Path is now gone & nothing came to output.
    assert not build_file.exists()

    captured = capsys.readouterr()
    assert captured.out == ""


def test_clean_verbose(configuration, recipes, mock_input, capsys):
    """Test clean with verbose flag."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=True)

    # Test
    clean(configuration, step).run()

    # Confirm verbose output:
    captured = capsys.readouterr()
    assert "Running " in captured.out
    assert "✔" in captured.out


def test_clean_confirm(configuration, recipes, mock_input, capsys, build_file):
    """Test clean with confirmation."""
    # Setup
    step = Step(method="aMethod", confirm=True, verbose=False)

    # Test
    mock_input.return_value = "yes"
    clean(configuration, step).run()

    # Confirm confirm message
    assert not build_file.exists()
    captured = capsys.readouterr()
    assert "Ok to " in captured.out
    assert "Running " not in captured.out


def test_clean_dryrun(recipes, mock_input, capsys, build_file):
    """Test clean with dry-run."""
    # Setup
    configuration = Configuration(dry_run=True)
    step = Step(method="aMethod", confirm=False, verbose=False)

    # Test
    clean(configuration, step).run()

    # Confirm dry-run message
    captured = capsys.readouterr()
    assert "DRY-RUN " in captured.out
    assert "✔" in captured.out
    assert build_file.exists()


def test_clean_confirm_verbose(configuration, recipes, mock_input, capsys):
    """Test clean with both confirm and verbose."""
    # Setup
    step = Step(method="aMethod", confirm=True, verbose=True)

    # Test
    mock_input.return_value = "y"
    clean(configuration, step).run()

    # Confirm confirm and verbose output
    captured = capsys.readouterr()
    assert "Ok to " in captured.out
    assert "Running " in captured.out
