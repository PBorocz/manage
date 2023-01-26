"""Core dispatch method that runs the primary processing loop."""
from models import Configuration


def dispatch(configuration: Configuration, recipes: dict, target: str) -> None:
    """Iterate (ie. execute) each step in the selected target's recipes for the specified package."""
    for step in recipes.get(target).get("steps"):
        assert "step" in step or "method" in step, f"Sorry, one of '{target}'s steps is missing 'step' or 'method'."

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
