"""Core processing loop to dispatch steps or methods for the selected recipe."""
from manage.models import Configuration


def dispatch(configuration: Configuration, recipes: dict, args_recipe: str) -> None:
    """Iterate, ie. execute, each step defined for the recipe specified."""

    # Check for special "no-op" recipes (for now, just "check")
    if args_recipe.casefold() in ("check"):
        return  # We've already run setup which does all of our validations

    for step in recipes.find_recipe(args_recipe).steps:

        # This step could be either a request to invoke a particular method OR a request to run another step
        if step.callable_:
            # Run the method already associated with the step:
            step.callable_(configuration, step)
        else:
            # Run another step!
            dispatch(configuration, recipes, step.step)

        # No need for else here as we've already validated the recipe file.
