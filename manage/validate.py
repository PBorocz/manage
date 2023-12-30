"""Validation, both overall environment and method specific."""
import os
import shutil
from pathlib import Path
from typing import TypeVar

from manage.models import Configuration, Recipes
from manage.utilities import failure, message, msg_failure, msg_debug, msg_warning, success, warning

TClass = TypeVar("Class")
TWarnsFails = tuple[list[str], list[str]]


def validate(configuration: Configuration, recipes: Recipes, method_classes: dict[str, TClass]) -> bool:
    """Run the complete validation suite, returning False if anything's wrong."""
    if configuration.verbose:
        message("Validating environment & recipes")

    warnings, failures = [], []

    # Check: How is our environment?
    warns, fails = _validate_environment(configuration)
    warnings.extend(warns)
    failures.extend(fails)

    # Check: are any step command-line arguments correct?
    warns, fails = _validate_step_args(configuration, method_classes)
    warnings.extend(warns)
    failures.extend(fails)

    # Check: are the methods/steps from our recipe file matched to actual method-classes?
    warns, fails = _validate_recipes(recipes, method_classes)
    warnings.extend(warns)
    failures.extend(fails)

    # Check: Do any of method_classes have validation logic to run?
    warns, fails = _validate_method_classes(configuration, recipes, method_classes)
    warnings.extend(warns)
    failures.extend(fails)

    # Check: are version numbers consistent between pyproject.toml and README's change history?
    warns, fails = _validate_existing_version_numbers(configuration)
    warnings.extend(warns)
    failures.extend(fails)

    if configuration.verbose:
        if failures:
            failure()
        elif warnings:
            warning()
        else:
            success()

    for msg in warnings:
        msg_warning(f"- {msg}")

    for msg in failures:
        msg_failure(f"- {msg}")

    if failures:
        return False
    return True


################################################################################
# Environment validation
################################################################################
def _validate_environment(configuration: Configuration) -> TWarnsFails:
    """Validate that our run-time environment is copacetic."""
    warns = []

    ################################################################################
    # Check Github configuration environment variables..
    ################################################################################
    for env_var in [
        "GITHUB_API_RELEASES",
        "GITHUB_USER",
        "GITHUB_API_TOKEN",
        "GITHUB_PROJECT_RELEASE_HISTORY",
    ]:
        if env_var not in os.environ:
            warns.append(f"Can't find environment variable '[italic]{env_var}[/]'")

    ################################################################################
    # Check for various executable:
    ################################################################################
    # Check we have a poetry on our path to run against..
    for executable in ["poetry", "git", "pandoc", "sass"]:
        if not shutil.which(executable):
            warns.append("[italic]{executable}[/] on your path, some methods won't work.")

    return warns, []


################################################################################
# CLI step arguments
################################################################################
def _validate_step_args(configuration: Configuration, method_classes: dict[str, TClass]) -> TWarnsFails:
    """Validate all cli dynamic/step arguments against our Method Classes."""

    def __get_all_args() -> list[tuple[str, str]]:
        return_ = []
        for method, class_ in method_classes.items():
            if not hasattr(class_, "args"):
                continue
            for arg in class_.args:
                return_.append((method.casefold(), arg.name.casefold()))
        return return_

    args_possible = __get_all_args()

    # Confirm dynamic/method arguments:
    fails = []
    for (method, arg), _ in configuration.method_args:  # e.g. ("git_commit", "message"), "aMessage"
        # 1. Confirm all method args are actually bound to know methods:
        if method.casefold() not in method_classes:
            fail = f"'[italic]{method}[/]' is not a recognised method, please check."
            fails.append(fail)
            continue

        # 2. Confirm that the argument provided is valid for the respective method/class:
        if (method.casefold(), arg.casefold()) not in args_possible:
            fail = f"'[italic]{arg}[/]' is not a valid argument for '[italic]{method}[/]', please check."
            fails.append(fail)

    return [], fails


################################################################################
# Method classes
################################################################################
def _validate_method_classes(
    configuration: Configuration,
    recipes: Recipes,
    method_classes: dict[str, TClass],
) -> TWarnsFails:
    """Find and run all 'validate' methods defined on our Method Classes."""
    fails = []
    for method, class_ in method_classes.items():
        instance = class_(configuration, recipes, {})  # Don't need "step" arg here..
        if validate_method := getattr(instance, "validate", None):
            if results := validate_method():
                fails.extend(results)
    return [], fails


################################################################################
# Recipes themselves..
################################################################################
def _validate_recipes(recipes: Recipes, method_classes_defined: dict[str, TClass]) -> TWarnsFails:
    """Make sure all the the methods and steps from our recipes are defined and available."""
    fails = list()
    for id_, recipe in recipes:
        for step in recipe:
            if step.method:
                if step.method not in method_classes_defined:
                    fails.append(f"Method: '{step.method}' in recipe={id_} is NOT a valid step method!")
            else:
                if recipes.get(step.recipe) is None:
                    fails.append(f"Step: '{step.recipe}' in recipe={id_} can't be found in this file!")
    return [], fails


################################################################################
# Version number validation...
################################################################################
def _validate_existing_version_numbers(configuration: Configuration) -> TWarnsFails:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml."""
    last_release_version = __get_last_release_from_readme()
    if last_release_version != configuration.version_:
        msg = (
            f"Warning, pyproject.toml has version: [italic]{configuration.version_}[/] "
            f"while last release in README is [italic]{last_release_version}[/]"
        )
        return [msg], []
    return [], []


def __get_last_release_from_readme() -> [str, str]:
    """Mini state-machine to find last "release" in our changelog embedded within our README."""
    debug = False
    path_readme = Path.cwd() / "README.md"
    format_ = "markdown"
    if not path_readme.exists():
        path_readme = Path.cwd() / "README.org"
        format_ = "org"
        if not path_readme.exists():
            msg_failure(
                "Sorry, unable to open EITHER README.md or README.org from the current directory.",
            )
            return path_readme, None

    if debug:
        msg_debug(f"\nReading from {path_readme}")

    method = __get_last_release_from_markdown if format_ == "markdown" else __get_last_release_from_org
    return method(path_readme)


def __get_last_release_from_org(path_readme: Path) -> str:
    debug = False
    header = "***"
    unreleased_header = f"{header} Unreleased".casefold()
    take_next_release = False
    for i_line, line in enumerate(path_readme.read_text().split("\n")):
        if line.casefold().startswith(unreleased_header):
            take_next_release = True
            if debug:
                msg_debug(f"Found '{unreleased_header}' on line: {i_line+1}")
            continue
        if take_next_release and line.casefold().startswith(header):  # eg "*** vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            if debug:
                msg_debug(f"Found next header matching '{line}' on line: {i_line+1}")
            return version
    return None


def __get_last_release_from_markdown(path_readme: Path) -> str:
    debug = False
    header = "###"
    unreleased_header = f"{header} Unreleased".casefold()
    take_next_release = False
    for i_line, line in enumerate(path_readme.read_text().split("\n")):
        if line.casefold().startswith(unreleased_header):
            take_next_release = True
            if debug:
                msg_debug(f"Found '{unreleased_header}' on line: {i_line+1}")
            continue
        if take_next_release and line.startswith(header):  # eg "### vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            if debug:
                msg_debug(f"Found next header matching '{line}' on line: {i_line+1}")
            return version
    return None
