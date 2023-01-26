"""Clean step"""
from manage.models import Configuration
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Clean the build environment."""
    if step.get("confirm", False):
        if not ask_confirm("Ok to clean build environment?"):
            return False
    return run(step, "rm -rf build *.egg-info")[0]
