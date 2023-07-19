"""Method to run SASS pre-processor."""
import shutil

from manage.models import Argument, Arguments, Configuration, Recipes
from manage.utilities import ask_confirm, message, run


# Metadata about arguments available...
args = Arguments(arguments=[
    Argument(
        name="pathspec",
        type_=str,
        default=None,
    ),
])

def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Run a SASS pre-processor command on the required pathspec."""
    # Check we have a SASS to run against..
    if not shutil.which("sass"):
        message("Sorry, we can't find 'sass' on your path.", color="red", end_failure=True)
        return False

    # Check for argument..
    if not (pathspec := step.get_arg('pathspec')):
        message("Sorry, the `sass` method requires a 'pathspec' argument.", color="red", end_failure=True)
        return False

    confirm = f"Ok to run '[italic]sass {pathspec}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False

    return run(step, f"sass {pathspec}")[0]
