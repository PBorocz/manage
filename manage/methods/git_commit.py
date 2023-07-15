"""General git commit."""
from datetime import datetime
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run

PATHSPEC_ALL = "."

def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Commits specified files."""
    if step.arguments and 'pathspec' in step.arguments:
        pathspec = step.arguments.get('pathspec')
    else:
        pathspec = PATHSPEC_ALL

    if step.arguments and 'message' in step.arguments:
        message = step.arguments.get('message')
    else:
        message = f"Commit as of {datetime.now.isformat()}"

    if step.confirm:
        confirm = "Ok to git commit all files?" if pathspec == PATHSPEC_ALL else f"Ok to git commit {pathspec}?"
        if not ask_confirm(confirm):
            return False

    return run(step, f'git commit --message "{message}" {pathspec}')[0]
