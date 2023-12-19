"""Core processing loop to dispatch recipe method(s) and/or step(s)."""

from manage.models import Configuration, Recipes
# from manage.methods._print import main as _print
# from manage.methods._check import main as _check


def dispatch(configuration: Configuration, recipes: Recipes) -> None:
    """Iterate, ie. execute, each step defined for the recipe specified."""
    # Check for special built-in recipes:
    # if configuration.target.casefold() in ("check"):
    #     return _check(configuration, recipes, None)

    # if configuration.target.casefold() in ("print"):
    #     return _print(configuration, recipes, None)

    # We have a "regular" step to be performed, could still be either a method OR another step though!
    for step in recipes.get(configuration.target):
        # Before we execute, update step with any/all runtime arguments received from the command line:
        # (while we "could" do this once on setup
        step.reflect_runtime_arguments(configuration)

        if step.class_:
            # Instantiate the method's class associated with the step
            instance = step.class_(configuration, recipes, step)
            # And execute the run method!
            instance.run()
        else:
            # Run another recipe!
            configuration.target = step.recipe  # Override the target (but leave the rest)
            dispatch(configuration, recipes)
