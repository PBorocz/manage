from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    if step.confirm:
        if not ask_confirm("Ok to run pre-commit?"):
            return False
    return run(step, "pre-commit run --all-files")[0]
