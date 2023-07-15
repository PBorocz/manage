"""Method to run SASS pre-processor."""
import shutil

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, message, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Run a SASS pre-processor command on the required pathspec."""
    # Check we have a SASS to run against..
    if not shutil.which("sass"):
        message("Sorry, we can't find 'sass' on your path.", color="red", end_failure=True)
        return False

    # Check for argument..
    if not step.arguments or 'pathspec' not in step.arguments:
        message("Sorry, we require a 'pathspec' entry in the arguments for this method.", color="red", end_failure=True)
        return False

    pathspec = step.arguments.get('pathspec')

    if step.confirm:
        confirm = f"Ok to run [italic]`sass {pathspec}`[/]?"
        if not ask_confirm(confirm):
            return False

    return run(step, f"sass {pathspec}")[0]
