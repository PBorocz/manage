"""Test cli methods."""
import tomllib
from pathlib import Path

from manage.models import PyProject


def test_internal_defaults():
    # Setup
    pyproject = PyProject.factory({})

    # Test
    assert pyproject.get_parm("verbose") is False
    assert pyproject.get_parm("confirm") is False
    assert pyproject.get_parm("dry_run") is True


def test_override():
    # Setup
    raw_pp = {"tool": {"manage": {"defaults": {"confirm": True, "verbose": True}}}}
    pyproject = PyProject.factory(raw_pp)

    # Test
    assert pyproject.get_parm("verbose") is True
    assert pyproject.get_parm("confirm") is True
    assert pyproject.get_parm("dry_run") is True


def test_validation_no_recipes(capsys):
    # Setup
    pyproject = PyProject.factory({})

    # Test
    assert not pyproject.validate()
    captured = capsys.readouterr()
    assert "No recipes found" in captured.out


def test_validation_invalid_default(capsys):
    # Setup
    raw_pp = {"tool": {"manage": {"defaults": {"UNKNOWN": True}}}}
    pyproject = PyProject.factory(raw_pp)

    # Test
    assert not pyproject.validate()
    captured = capsys.readouterr()
    assert "UNKNOWN" in captured.out


def test_validation_no_package(capsys):
    # Setup
    raw_pp = tomllib.loads(Path("tests/test_models_pyproject_no_package.toml").read_text())
    pyproject = PyProject.factory(raw_pp)

    # Test
    assert pyproject.validate()
    captured = capsys.readouterr()
    assert "No 'packages' entry found in [tool.poetry]" in captured.out


def test_validation_no_version(capsys):
    # Setup
    raw_pp = tomllib.loads(Path("tests/test_models_pyproject_no_version.toml").read_text())
    pyproject = PyProject.factory(raw_pp)

    # Test
    assert pyproject.validate()
    captured = capsys.readouterr()
    assert "No version label found in [tool.poetry]" in captured.out
