from models import Configuration
from utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Have poetry push/publish/upload to pypi"""
    if step.get("confirm", False):
        if not ask_confirm("Ok to publish to PyPI?"):
            return False
    return run(step, "poetry publish")[0]
