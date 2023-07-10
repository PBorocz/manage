"""Command test."""
from pathlib import Path

import pytest

from manage.models import Configuration, Recipes, Step
from manage.methods.update_readme import main as update_readme


test_readme_md = """
## Release History

### Unreleased
   - [[https://towardsdatascience.com/should-we-use-custom-exceptions-in-python-b4b4bca474ac][custom exceptions]]

### v1.9.10
   - open text open text open text open text open text open text open text open text open text open text open text.

### v1.9.09
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


def test_md(path_readme_md):
    # Setup
    step = Step(method="aMethod", confirm=False, quiet_mode=True, arguments=dict(readme_format="md", cwd="/tmp"))

    # Test
    assert update_readme(Configuration(version_="1.9.11"), Recipes.parse_obj({}), step)

    # Confirm
    assert path_readme_md.exists()

    readme = path_readme_md.read_text()
    assert "### Unreleased" in readme
    assert "v1.9.11" in readme


def test_org(path_readme_org):
    # Setup
    step = Step(method="aMethod", confirm=False, quiet_mode=True, arguments=dict(readme_format="org", cwd="/tmp"))

    # Test
    assert update_readme(Configuration(version_="1.9.11"), Recipes.parse_obj({}), step)

    # Confirm
    assert path_readme_org.exists()

    readme = path_readme_org.read_text()
    assert "*** Unreleased" in readme
    assert "v1.9.11" in readme
