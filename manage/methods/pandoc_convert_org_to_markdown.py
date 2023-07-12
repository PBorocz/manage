"""Convert an emacs org file into a markdown version using Pandoc."""
from rich import print

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, _, step: dict) -> bool:
    """Do step."""
    assert step.arguments, "Sorry, this command requires supplement arguments"
    assert 'path_org' in step.arguments, "Sorry, command requires a supplemental argument for 'path_org'"
    assert 'path_md' in step.arguments, "Sorry, command requires a supplemental argument for 'path_md'"

    path_md = step.get_arg('path_md')
    path_org = step.get_arg('path_org')

    try:
        return run(step, f"pandoc -f org -t markdown --wrap none --output {path_md} {path_org}")[0]
    except FileNotFoundError:
        print("\n[red]Sorry, couldn't find a [italic]pandoc[/] executable on your path!")
        return False
