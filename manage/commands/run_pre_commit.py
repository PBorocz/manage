from models import Configuration
from utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    if step.get("confirm", False):
        if not ask_confirm("Ok to run pre-commit?"):
            return False
    return run(step, "pre-commit run --all-files")[0]
