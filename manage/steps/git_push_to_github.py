from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Push to github"""
    if step.confirm:
        if not ask_confirm("Ok to push to github?"):
            return False
    return run(step, "git push --follow-tags")[0]
