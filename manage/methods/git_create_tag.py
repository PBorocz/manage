"""Create git tag, i.e. v<major>.<minor>.<patch>."""
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Create git tag, i.e. v<major>.<minor>.<patch>."""
    tag = configuration.version
    confirm = f"Ok to create tag in git of '[italic]{tag}[/]'?"
    if step.confirm and not ask_confirm(confirm):
        return False
    return run(step, f"git tag -a {tag} --message {tag}")[0]
