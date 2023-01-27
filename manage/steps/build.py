from manage.models import Configuration
from manage.utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Build the distribution"""
    if step.confirm:
        if not ask_confirm("Ok to build distribution files?"):
            return False
    return run(step, "poetry build")[0]
