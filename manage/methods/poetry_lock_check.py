"""Verify that poetry.lock is consistent with pyproject.toml and update if not (good security practice)."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run, warning


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Poetry lock check and optional update."""
    # Initial check is easy...if it returns fine, we're done...otherwise, update it!
    if not run(step, "poetry lock --check")[0]:
        warning()
        print("[yellow]poetry.lock is not consistent with pyproject.toml.[/]")
        if step.confirm:
            if not ask_confirm("Can we run `poetry lock --no-update` to fix it?"):
                return False
        return run(step, "poetry lock --no-update")[0]
