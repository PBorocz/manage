from models import Configuration
from utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Push to github"""
    if step.get("confirm", False):
        if not ask_confirm("Ok to push to github?"):
            return False
    return run(step, "git push --follow-tags")[0]
