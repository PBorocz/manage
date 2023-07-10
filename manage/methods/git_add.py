"""Method to perform a 'git add' (aka stage) command."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run

PATHSPEC_ALL = "."

def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Do a 'git add' command, either with a specific wildcard or all (if no argument specified)."""
    if step.arguments and 'pathspec' in step.arguments:
        pathspec = step.arguments.get('pathspec')
    else:
        pathspec = PATHSPEC_ALL

    if step.confirm:
        confirm = "Ok to git add (stage) all files?" if pathspec == PATHSPEC_ALL else f"Ok to git add {pathspec}?"
        if not ask_confirm(confirm):
            return False

    return run(step, f"git add {pathspec}")[0]
