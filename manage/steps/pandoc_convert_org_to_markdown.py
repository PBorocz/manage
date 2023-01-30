"""Convert an ORG file into a MD (markdown) using Pandoc."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, _, step: dict) -> bool:
    """Do step."""
    assert hasattr(step, "args_"), "Sorry, this command requires supplement arguments"
    assert 'path_org' in step.args_, "Sorry, command requires a supplemental argument for 'path_org'"
    assert 'path_md' in step.args_, "Sorry, command requires a supplemental argument for 'path_md'"

    path_md = step.args_['path_md']
    path_org = step.args_['path_org']
    return run(step, f"pandoc -f org -t markdown --wrap none --output {path_md} {path_org}")[0]
