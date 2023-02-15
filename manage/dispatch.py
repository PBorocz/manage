"""Core processing loop to dispatch steps or methods for the selected recipe."""
import argparse

from manage.models import Configuration


def dispatch(configuration: Configuration, recipes: dict, args: argparse.Namespace) -> None:
    """Iterate, ie. execute, each step defined for the recipe specified."""

    # Check for special "no-op" recipes (for now, just "check")
    if args.target.casefold() in ("check"):
        return  # We've already run setup which does all of our validations

    if args.target.casefold() in ("print"):
        from rich import print
        print(recipes)
        return

    for step in recipes.get(args.target):
        if step.callable_:
            # Run the *method* associated with the step
            step.callable_(configuration, recipes, step)
        else:
            # Run another recipe!
            args.target = step.recipe  # Override the target (but leave the rest)
            dispatch(configuration, recipes, args)

        # No need for else here as we've already validated the recipe file.
