"""Command test."""
from pathlib import Path

import pytest

from manage.models import Configuration, Recipes, Step
from manage.methods.pandoc_convert_org_to_markdown import Method as pandoc_convert_org_to_markdown  # noqa: N813

test_org_text = """
* Sample ORG File
** SubHead 1
   - [[https://towardsdatascience.com/should-we-use-custom-exceptions-in-python-b4b4bca474ac][custom exceptions]]
** SubHead 2
*** SubHead2 - 1
    open text open text open text open text open text open text open text open text open text open text open text.
"""


@pytest.fixture
def path_md():
    path_md = Path("/tmp/test.md")
    yield path_md
    if path_md.exists():
        path_md.unlink()


@pytest.fixture
def path_org():
    path_org = Path("/tmp/test.org")
    path_org.write_text(test_org_text)
    yield path_org
    if path_org.exists():
        path_org.unlink()


def test_normal_case(path_org, path_md):
    # Setup
    step = Step(
        method="aMethod",
        confirm=False,
        verbose=False,
        arguments=dict(path_org=path_org, path_md=path_md),
    )

    # Test
    assert pandoc_convert_org_to_markdown(Configuration(), Recipes.parse_obj({}), step).run()

    # Confirm
    assert path_md.exists()

    md_ = path_md.read_text()
    assert "Sample ORG File" in md_
    assert "open text." in md_
    assert "[custom exceptions]" in md_


def test_missing_arg_s(path_org, path_md):
    # Setup
    step = Step(method="aMethod", confirm=False, verbose=False)

    # Test
    assert not pandoc_convert_org_to_markdown(Configuration(), Recipes.parse_obj({}), step).run()
