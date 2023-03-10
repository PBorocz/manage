from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Have poetry push/publish/upload to pypi"""
    if step.confirm:
        if not ask_confirm("Ok to publish to PyPI?"):
            return False
    return run(step, "poetry publish")[0]
