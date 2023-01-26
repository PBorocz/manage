from models import Configuration
from utilities import ask_confirm, run


def main(configuration: Configuration, step: dict) -> bool:
    """Create git tag, i.e. v<major>.<minor>.<patch>"""
    tag = configuration.version()
    if step.get("confirm", False):
        if not ask_confirm(f"Ok to create tag in git: {tag}?"):
            return False
    return run(step, f"git tag -a {tag} --message {tag}")[0]
