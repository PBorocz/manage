"""Command test."""
from pathlib import Path

import pytest

from manage.models import Configuration, Recipes, Step
from manage.methods.update_readme import main as update_readme


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
    path_ = Path("/tmp/README.org")
    path_.write_text(test_readme_org_no_header)
    yield path_
    if path_.exists():
        path_.unlink()


@pytest.fixture
def configuration():
    yield Configuration.factory(None, None, version_="1.9.11")


def test_md(configuration, path_readme_md):
    """Test standard case with Markdown file."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme=str(path_readme_md)))

    # Test
    assert update_readme(configuration, Recipes.parse_obj({}), step)

    # Confirm
    assert path_readme_md.exists()

    readme = path_readme_md.read_text()
    assert "## Unreleased" in readme  # Note: Second level header here!!
    assert "v1.9.11" in readme


def test_org(configuration, path_readme_org):
    """Test standard case with Org file."""
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme=str(path_readme_org)))

    # Test
    assert update_readme(configuration, Recipes.parse_obj({}), step)

    # Confirm
    assert path_readme_org.exists()

    readme = path_readme_org.read_text()
    assert "*** Unreleased" in readme  # Note: *THIRD* level header here!!
    assert "v1.9.11" in readme


def test_no_file_available(configuration):
    """Test case where we don't have a README at all!"""
    # Setup (note: we don't specify the name of the file here but we DO need to set cwd
    # so we don't accidentally pick up the README file in our own project!)
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(cwd="/tmp"))

    # Test
    assert not update_readme(configuration, Recipes.parse_obj({}), step)


def test_file_not_found(configuration):
    """Test case where we have a README specified but it doesn't actually exist."""
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme="/tmp/foobar"))

    # Test
    assert not update_readme(configuration, Recipes.parse_obj({}), step)


def test_no_unreleased_header(configuration, path_readme_org_no_header):
    """Test case where we have a README specified but it doesn't actually exist."""
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(readme=str(path_readme_org)))

    # Test
    assert not update_readme(configuration, Recipes.parse_obj({}), step)


def test_file_from_default(configuration, path_readme_md):
    """Test special case where we find a default README file (in this case, Markdown)."""
    # Setup (note: we don't specify the name of the file here!
    step = Step(method="aMethod", confirm=False, verbose=False, arguments=dict(cwd="/tmp"))

    # Test
    assert update_readme(configuration, Recipes.parse_obj({}), step)

    # Confirm
    assert path_readme_md.exists()

    readme = path_readme_md.read_text()
    assert "## Unreleased" in readme  # Note: Second level header here!!
    assert "v1.9.11" in readme
