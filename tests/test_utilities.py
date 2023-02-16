"""Tests for various methods in the utility library."""
from manage.utilities import parse_dynamic_argument, replace_rich_markup


def test_replace_rich_markup():
    """Test ability to remove rich markup from string."""
    cases = (
        ("[italic][/]", ""),
        ("before [italic]'in italic'[/] after", "before 'in italic' after"),
        ("before [italic]'in italic'[/] after [SomethingElse]asdfasf[/]", "before 'in italic' after asdfasf"),
    )
    for before, after in cases:
        assert replace_rich_markup(before) == after


def test_parse_dynamic_argument_typing():
    """Test parse_dynamic_argument."""
    cases = [
        ["anArgument"  , ["anArgument", str]],
        ["an_argument" , ["an_argument", str]],
        ["aStrArg_str" , ["aStrArg", str]],
        ["another_int" , ["another", int]],
        ["yes_no_bool" , ["yes_no", bool]],
    ]
    for input_, expected in cases:
        assert expected == parse_dynamic_argument(input_)
