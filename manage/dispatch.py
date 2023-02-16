"""Core processing loop to dispatch recipe method(s) and/or step(s)."""
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

    # We have a "regular" step to be performed, could still be either a method OR another step though!
    for step in recipes.get(args.target):

        # Before we execute, update step with any/all runtime arguments received from the command line:
        # (while we "could" do this once on setup
        step.reflect_runtime_arguments(args)

        if step.callable_:
            # Run the *method* associated with the step
            step.callable_(configuration, recipes, step)
        else:
            # Run another recipe!
            args.target = step.recipe  # Override the target (but leave the rest)
            dispatch(configuration, recipes, args)
