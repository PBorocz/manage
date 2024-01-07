"""Test cli methods."""
import tomllib
from pathlib import Path

from manage.models import PyProject


def test_validation_no_recipes(capsys):
    # Setup
    pyproject = PyProject.factory_from_raw({})

    # Test
    assert not pyproject.validate()
    captured = capsys.readouterr()
    assert "No recipes found" in captured.out


def test_validation_invalid_default(capsys):
    # Setup
    raw_pp = {"tool": {"manage": {"defaults": {"UNKNOWN": True}}}}
    pyproject = PyProject.factory_from_raw(raw_pp)

    # Test
    assert not pyproject.validate()
    captured = capsys.readouterr()
    assert "No recipes found" in captured.out


def test_validation_no_package(capsys):
    # Setup
    raw_pp = tomllib.loads(Path("tests/models/test_pyproject_no_package.toml").read_text())
    pyproject = PyProject.factory_from_raw(raw_pp)

    # Test
    assert pyproject.validate()
    captured = capsys.readouterr()
    assert "No 'packages' entry found in [tool.poetry]" in captured.out


def test_validation_no_version(capsys):
    # Setup
    raw_pp = tomllib.loads(Path("tests/models/test_pyproject_no_version.toml").read_text())
    pyproject = PyProject.factory_from_raw(raw_pp)

    # Test
    assert pyproject.validate()
    captured = capsys.readouterr()
    assert "No version label found in [tool.poetry]" in captured.out
