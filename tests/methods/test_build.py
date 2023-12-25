"""Test build method."""
import pytest
import tomllib
from pathlib import Path

from manage import DEFAULT_PROJECT_PATH
from manage.models import Configuration, Recipes, Step
from manage.methods.poetry_build import Method as build  # noqa: N813


@pytest.fixture
def configuration():
    return Configuration(dry_run=False)


@pytest.fixture
def recipes():
    return Recipes.parse_obj({})


def test_build(configuration, recipes, capsys):
    """Test build method."""
    ################################################################################
    # Setup
    ################################################################################
    step = Step(method="aMethod", confirm=False, verbose=False)

    # Get the current version from pyproject.toml
    raw_pyproject = tomllib.loads(DEFAULT_PROJECT_PATH.read_text())
    version = raw_pyproject.get("tool", {}).get("poetry", {}).get("version", None)

    path_whl = Path("dist") / Path(f"manage-{version}-py3-none-any.whl")
    path_tgz = Path("dist") / Path(f"manage-{version}.tar.gz")

    try:
        path_whl.unlink()
        path_tgz.unlink()
    except FileNotFoundError:
        ...

    ################################################################################
    # Test
    ################################################################################
    build(configuration, recipes, step).run()

    ################################################################################
    # Confirm: Build artifacts now exist
    ################################################################################
    assert path_whl.exists()
    assert path_tgz.exists()

    captured = capsys.readouterr()
    assert captured.out == ""
