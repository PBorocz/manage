"""Setup methods, not meant for direct calling from manage.toml."""
import importlib
import sys
from pathlib import Path
from typing import Optional, Callable

from tomli import load
from rich import print

from models import Configuration
from utilities import fmt, run, success, failure


def setup() -> tuple[Configuration, dict]:
    """Setup method, return steps/commands, current package name and recipe book."""

    # Confirm we're working from the README/root level of our project
    if not (Path.cwd() / "README.org").exists():
        print("[red]Sorry, we need run this from the same direction that your README.org file sits.")
        sys.exit(1)

    # Gather all available steps
    step_methods = _gather_available_steps()
    if not step_methods:
        sys.exit(1)

    # Read configuration and package we're working on
    package = _get_package_from_pyproject()
    if package is None:
        sys.exit(1)

    recipes = _read_recipes(step_methods)
    if recipes is None:
        sys.exit(1)

    recipes["__step_callables__"] = step_methods

    # Although we might update it as part of our steps, in case we don't, get the current version as of now:
    configuration = Configuration(
        _version=run(None, "poetry version --short")[-1],
        package=package,
    )

    return configuration, recipes


def _get_package_from_pyproject() -> Optional[str]:
    """Read the pyproject.toml file to return the name of the current package we're working with."""
    msg = fmt("Reading package name (pyproject.toml)", color='blue')
    print(msg, end="", flush=True)
    with open(Path("./pyproject.toml"), "rb") as fh_:
        pyproject = load(fh_)
    if packages := pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
        try:
            # FIXME: For now, we support the first entry in tool.poetry.packages
            #        (even though multiple are allowed)
            package_include = packages[0]
            package = package_include.get("include")
            success()
            return package
        except IndexError:
            ...
    failure()
    return None


def _gather_available_steps() -> dict[str, Callable]:
    msg = fmt("Reading available steps", color='blue')
    print(msg, flush=True, end="")
    return_ = dict()
    for pth in Path("manage/commands").glob('*.py'):
        if pth.name.startswith("__"):
            continue
        step_name = pth.stem
        module = importlib.import_module(f'commands.{step_name}')
        return_[step_name] = getattr(module, "main")
    if not return_:
        failure()
        print("[red]Unable to find any valid command steps in manage/commands/*.py?")
        sys.exit(1)
    success()
    return return_


def _read_recipes(steps_available: list[Callable]) -> dict:
    msg = fmt("Reading recipes (manage.toml)", color='blue')
    print(msg, flush=True, end="")
    try:
        with open("manage.toml", "rb") as stream:
            recipes = load(stream)
    except FileNotFoundError as err:
        failure()
        print(f"[red]{err}")
        sys.exit(1)
    success()

    # Make sure all the the methods and steps are defined and available:
    msg = fmt("Validating recipes", color='blue')
    print(msg, flush=True, end="")
    invalid_method_references = list()
    invalid_step_references = list()
    for target in sorted(list(recipes.keys())):
        for step in recipes.get(target).get("steps"):
            if "step" in step:
                step_name = step.get("step")
                if step_name not in recipes:
                    invalid_step_references.append(step_name)
            elif "method" in step:
                method_name = step.get("method")
                if method_name not in steps_available:
                    invalid_method_references.append(method_name)

    if invalid_method_references or invalid_step_references:
        if invalid_method_references:
            print("\n[red]Sorry, error in manage.toml; The following method(s) can't be found:")
            for method_name in invalid_method_references:
                print(f"[red]- {method_name}")
        if invalid_step_references:
            print("\n[red]Sorry, error in manage.toml; The following step(s) can't be found:")
            for step_name in invalid_step_references:
                print(f"[red]- {step_name}")
        failure()
        return None

    success()
    return recipes
