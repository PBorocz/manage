"""Command test."""
from pathlib import Path

import pytest

from manage.models import Configuration, Step
from manage.methods.update_readme import Method as update_readme  # noqa: N813


test_readme_md = """
# Release History

## Unreleased
   - [[https://towardsdatascience.com/should-we-use-custom-exceptions-in-python-b4b4bca474ac][custom exceptions]]

## v1.9.10
   - open text open text open text open text open text open text open text open text open text open text open text.

## v1.9.09
   - open text open text open text open text open text open text open text open text open text open text open text.
"""

test_readme_org = """
** Release History

*** Unreleased
   - [[https://towardsdatascience.com/should-we-use-custom-exceptions-in-python-b4b4bca474ac][custom exceptions]]

*** v1.9.10
   - open text open text open text open text open text open text open text open text open text open text open text.

*** v1.9.09
   - open text open text open text open text open text open text open text open text open text open text open text.
"""

test_readme_org_no_header = """
** Release History

*** v1.9.10
   - open text open text open text open text open text open text open text open text open text open text open text.

*** v1.9.09
   - open text open text open text open text open text open text open text open text open text open text open text.
"""

pyproject_toml = """
[tool.poetry]
name = "myPackage"
version = "1.9.11"
description = "Sample pyproject.toml"
"""


@pytest.fixture
def path_readme_md():
    path_ = Path("/tmp/README.md")
    path_.write_text(test_readme_md)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def path_readme_org():
    path_ = Path("/tmp/README.org")
    path_.write_text(test_readme_org)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def path_readme_org_no_header():
    path_ = Path("/tmp/pyproject.toml")
    path_.write_text(pyproject_toml)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def path_pyproject():
    path_ = Path("/tmp/pyproject.toml")
    path_.write_text(pyproject_toml)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def configuration():
    yield Configuration.factory([None, []], dry_run=False)


def test_md(path_pyproject, configuration, path_readme_md):
    """Test standard case with Markdown file."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme=str(path_readme_md)))

    # Test
    assert update_readme(configuration, step).run(path_pyproject=path_pyproject)

    # Confirm we still have a readme file..
    assert path_readme_md.exists()

    # Confirm that it's been updated to (a) have our new release and (b) still have an Unreleased section.
    readme = path_readme_md.read_text()
    assert "v1.9.11" in readme
    assert "## Unreleased" in readme  # Note: Second level header here!!


def test_org(path_pyproject, configuration, path_readme_org):
    """Test standard case with Org file."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme=str(path_readme_org)))

    # Test
    assert update_readme(configuration, step).run(path_pyproject=path_pyproject)

    # Confirm
    assert path_readme_org.exists()

    readme = path_readme_org.read_text()
    assert "*** Unreleased" in readme  # Note: *THIRD* level header here!!
    assert "v1.9.11" in readme


def test_file_not_found(configuration):
    """Test case where we have a README specified but it doesn't actually exist."""
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme="/tmp/foobar"))

    # Test
    result = update_readme(configuration, step).validate()
    assert len(result) == 1
    assert "Sorry, path" in result[0]
    assert "/tmp/foobar" in result[0]


def test_no_unreleased_header(path_pyproject, configuration, path_readme_org_no_header):
    """Test case where we have a README specified but it doesn't actually exist."""
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme=str(path_readme_org_no_header)))

    # Test
    assert not update_readme(configuration, step).run(path_pyproject=path_pyproject)


#
# FIXME: Should get this to work!
#
# def test_file_from_default(configuration, path_readme_md):
#     """Test special case where we find a default README file (in this case, Markdown)."""
#     # Setup (note: we don't specify the name of the file here!
#     step = Step(method="aMethod", confirm=False, verbose=False, arguments={})

#     # Test
#     assert update_readme(configuration, step).run()

#     # Confirm
#     assert path_readme_md.exists()

#     readme = path_readme_md.read_text()
#     assert "## Unreleased" in readme  # Note: Second level header here!!
#     assert "v1.9.11" in readme
