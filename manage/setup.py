"""Setup methods, not meant for direct calling from manage.toml."""
import importlib
import sys
from pathlib import Path
from typing import Callable

from tomli import load
from rich import print

from manage.models import Configuration
from manage.utilities import fmt, success, failure

UNRELEASED_HEADER = "*** Unreleased"
PATH_README = Path.cwd() / "README.org"


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
    configuration = _get_package_version_from_pyproject()
    if configuration is None:
        sys.exit(1)

    recipes = _gather_recipes(step_methods)
    if recipes is None:
        sys.exit(1)

    recipes["__step_callables__"] = step_methods

    # Validate that version numbers are consistent between pyproject.toml and README's change history.
    if not _validate_existing_version_numbers(configuration):
        sys.exit(1)

    return configuration, recipes


def __get_last_release_from_readme() -> str:
    """Mini state-machine to find last "release" in our changelog embedded within our README."""
    take_next_release = False
    for line in PATH_README.read_text().split("\n"):
        if line.startswith(UNRELEASED_HEADER):
            take_next_release = True
            continue
        if take_next_release and line.startswith("*** "):  # eg "*** vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            return version
    return None


def _validate_existing_version_numbers(configuration: Configuration) -> bool:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml"""
    msg = fmt("Checking consistency of versions (pyproject.toml & README.org)", color='blue')
    print(msg, end="", flush=True)
    last_release_version = __get_last_release_from_readme()
    if last_release_version != configuration._version:
        failure()
        print(f"[red]Warning, pyproject.toml has version: {configuration._version} while last release in README is {last_release_version}!")
        return False

    success()
    return True


def _get_package_version_from_pyproject() -> Configuration:
    """Read the pyproject.toml file to return current package and version we're working with."""
    msg = fmt("Reading package & version (pyproject.toml)", color='blue')
    print(msg, end="", flush=True)
    with open(Path("./pyproject.toml"), "rb") as fh_:
        pyproject = load(fh_)

    # Lookup the package which "should" represent the current package we're working on:
    package = None
    if packages := pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
        try:
            # FIXME: For now, we support the first entry in tool.poetry.packages
            #        (even though multiple are allowed)
            package_include = packages[0]
            package = package_include.get("include")
        except IndexError:
            ...

    # Similarly, get our current version:
    version = pyproject.get("tool", {}).get("poetry", {}).get("version", None)

    if package and version:
        success()
        return Configuration(_version=version, package=package)

    if package is None:
        print("[red]Sorry, unable to find a valid 'packages' entry under [tool.poetry] in pyproject.toml!")
    if version is None:
        print("[red]Sorry, unable to find a valid version entry under [tool.poetry] in pyproject.toml")

    failure()
    return None


def _gather_available_steps() -> dict[str, Callable]:
    msg = fmt("Reading recipe steps available", color='blue')
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


def _gather_recipes(steps_available: list[Callable]) -> dict:
    """Gather all recipes current available in our recipes file, including "system" ones we add here!"""
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

    # Make sure all the the methods and steps from our recipes are defined and available:
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

    # Add in any "system" recipes
    recipes["check"] = dict(
        name="Check configuration",
        description="Only executes setup and configuration/validation steps",
        steps=[dict(method=None, built_in=True),]
    )

    return recipes
