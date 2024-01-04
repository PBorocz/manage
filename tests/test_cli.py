"""Test cli methods."""
from manage.cli import do_help
from manage.models import Configuration, PyProject


def test_help(capsys):
    # Setup
    configuration = Configuration.factory([{}, []], {}, test=True)
    do_help(configuration, PyProject(), {})
    captured = capsys.readouterr()
    assert "OPTIONS" in captured.out
    assert "RECIPES" in captured.out


#
# Alternative approaches of capturing what's getting written out:
# (all should work)
#
# def test_help_console(pyproject):
#     console = Console()
#     with console.capture() as capture:
#         do_help(PyProject(), console)
#     table_str = capture.get()
#     assert table_str
#
# def test_help_stdout(capsys):  # or use "capfd" for fd-level
#     print("hello")
#     sys.stderr.write("world\n")
#     captured = capsys.readouterr()
#     assert captured.out == "hello\n"
#     assert captured.err == "world\n"
#     print("next")
#     captured = capsys.readouterr()
#     assert captured.out == "next\n"
