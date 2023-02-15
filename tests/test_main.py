import os
import sys
from pathlib import Path
from unittest.mock import patch

import pydantic
import pytest

from manage.cli import main


def test_wrong_directory(capsys):
    """Test when main is running from the wrong directory."""
    # Setup
    with patch.object(Path, 'cwd') as mock_cwd:
        mock_cwd.return_value = Path("/tmp")
        # Test
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main()
            # Confirm
            out, err = capsys.readouterr()
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 1
            assert "you need to run this from the same directory" in out


def test_get_recipes_args_no_recipe_file(capsys):
    """Test main for no recipe file."""
    # Setup
    argv = ["poetry_manage/manage/__main__.py", "build", "--recipes", "/tmp/fubar.does.not.exist"]
    with patch.object(sys, 'argv', argv):
        # Test
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main()
            # Confirm
            out, err = capsys.readouterr()
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 1
            assert "unable to find" in out


def test_invalid_target(capsys):
    """Test main for invalid target."""
    # Setup
    argv = ["poetry_manage/manage/__main__.py", "sdfasdfasdf"]
    with patch.object(sys, 'argv', argv):
        # Test
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main()
            # Confirm
            out, err = capsys.readouterr()
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 1
            assert "is not a valid recipe" in out
