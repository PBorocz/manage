"""Command test."""
from pathlib import Path

import pytest

from manage.models import Configuration, Step
from manage.methods.poetry_version_sync import Method as poetry_version_sync  # noqa: N813


init_base = """
# Test __init__.py file

foo = "bar"
__version__ = "oldVersion"
bar = 1.234
"""

init_no_version = """
# Test __init__.py file without a __version__ line.

foo = "bar"
bar = 1.234
"""


@pytest.fixture
def path_init_base():
    path_ = Path("/tmp/__init__.py")
    path_.write_text(init_base)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def path_init_no_version():
    path_ = Path("/tmp/__init__.py")
    path_.write_text(init_no_version)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def configuration():
    yield Configuration.factory([None, []], None, version_="M.m.p", dry_run=False)


def test_init_base(configuration, path_init_base):
    """Test standard case."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(init_path=str(path_init_base)))

    # Test
    result = poetry_version_sync(configuration, step).run()

    # Confirm
    assert result

    # Do we still have a __init__ file..
    assert path_init_base.exists()

    # Make sure that it's been updated to have our new version value (from configuration fixture above)
    init_ = path_init_base.read_text()
    assert '__version__ = "M.m.p"' in init_
    assert "foo = " in init_
    assert "bar = " in init_


def test_no_version(configuration, path_init_no_version):
    """Test case where we have a README specified but it doesn't actually exist."""
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(init_path=str(path_init_no_version)))

    # Test
    assert not poetry_version_sync(configuration, step).run()


def test_file_not_found(configuration):
    """Test case where we have a __init__ specified but it doesn't actually exist."""
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme="/tmp/foobar"))

    # Test
    assert not poetry_version_sync(configuration, step).validate()
