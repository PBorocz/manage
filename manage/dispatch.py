"""Core processing loop to dispatch steps or methods for the selected recipe."""
from manage.models import Configuration


def dispatch(configuration: Configuration, recipes: dict, args_recipe: str) -> None:
    """Iterate, ie. execute, each step defined for the recipe specified."""

    # Check for special "no-op" recipes (for now, just "check")
    if args_recipe.casefold() in ("check"):
        return  # We've already run setup which does all of our validations

    if args_recipe.casefold() in ("print"):
        from rich import print
        print(recipes)
        return

    for step in recipes.get(args_recipe):
        if step.callable_:
            # Run the *method* associated with the step
            step.callable_(configuration, step)
        else:
            # Run another step!
            dispatch(configuration, recipes, step.action)

        # No need for else here as we've already validated the recipe file.
