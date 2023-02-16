
from manage.utilities import parse_dynamic_argument


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
