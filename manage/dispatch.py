"""Core processing loop to dispatch recipe method(s) and/or step(s)."""

from manage.models import Configuration, Recipes


def dispatch(configuration: Configuration, recipes: Recipes) -> None:
    """Iterate, ie. execute, each step defined for the recipe specified."""
    for step in recipes.get(configuration.target):
        # Each step to be performed could be either a method OR another step:
        if step.class_:
            # Instantiate the method's class associated with the step and execute the "run" method!
            step.class_(configuration, recipes, step).run()
        else:
            # Run another recipe!
            configuration.target = step.recipe  # Override the target (but leave the rest)
            dispatch(configuration, recipes)
