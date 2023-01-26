"""Core processing loop to dispatch steps or methods for the selected recipe."""
from manage.models import Configuration


def dispatch(configuration: Configuration, recipes: dict, recipe: str) -> None:
    """Iterate, ie. execute, each step defined for the recipe specified."""

    # Check for special "no-op" recipes (for now, just "check")
    if recipe.casefold() in ("check"):
        return  # We've already run setup which does all of our validations

    for step in recipes.get(recipe).get("steps"):

        # This step could be either a request to invoke a particular method OR a request to run another step
        if "method" in step:
            # Lookup and run the method associated with the step:
            method_name = step.get("method")
            method = recipes.get("__step_callables__").get(method_name)
            if method is None:
                raise RuntimeError(f"Sorry, unable to find method: '{method_name}'")
            method(configuration, step)

        elif "step" in step:
            # Run another step!
            dispatch(configuration, recipes, step.get("step"))

        # No need for else here as we've already validated the recipe file.
