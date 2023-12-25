"""Validation, both overall environment and method specific."""
import os
import shutil
from pathlib import Path
from typing import TypeVar

from manage.models import Configuration, Recipes
from manage.utilities import failure, message, success, v_message, warning

TClass = TypeVar("Class")


def validate(configuration: Configuration, recipes: Recipes, method_classes: dict[str, TClass]) -> bool:
    """Run the complete validation suite, returning False if anything's wrong."""
    all_ok = True

    v_message(configuration.verbose, "Validating environment & recipes")

    # Check: How is our environment?
    if not _validate_environment(configuration):
        all_ok = False

    # Check: are any step command-line arguments correct?
    if not _validate_step_args(configuration, method_classes):
        all_ok = False

    # Check: are the methods/steps from our recipe file matched to actual method-classes?
    if not _validate_recipes(recipes, method_classes):
        all_ok = False

    # Check: Do any of method_classes have validation logic to run?
    if not _validate_method_classes(configuration, recipes, method_classes):
        all_ok = False

    # Check: are version numbers consistent between pyproject.toml and README's change history?
    if not _validate_existing_version_numbers(configuration):
        all_ok = False

    if configuration.verbose and all_ok:
        success()

    return all_ok


################################################################################
# Environment validation
################################################################################
def _validate_environment(configuration: Configuration) -> bool:
    """Validate that our run-time environment is copacetic."""
    messages = []

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
            messages.append(f"Can't find environment variable '[italic]{env_var}[/]'")

    ################################################################################
    # Check for various executable:
    ################################################################################
    # Check we have a poetry on our path to run against..
    for executable in ["poetry", "git", "pandoc", "sass"]:
        if not shutil.which(executable):
            messages.append("Can't find [italic]{executable}[/] on your path.")

    if not messages:
        return True

    warning()
    for msg in messages:
        message(f"- {msg}", color="yellow", end_warning=True)
    return False


################################################################################
# CLI step arguments
################################################################################
def _validate_step_args(configuration: Configuration, method_classes: dict[str, TClass]) -> bool:
    """Validate all cli dynamic/step arguments against our Method Classes."""

    def __get_all_args() -> list[str]:
        return_ = []
        for method, class_ in method_classes.items():
            if not hasattr(class_, "args"):
                continue
            for arg in class_.args:
                return_.append(arg.name)
        return return_

    args_possible = __get_all_args()

    # Confirm all method args show up in *any* method_class.
    invalid = []
    for arg_name in configuration.method_args.keys():
        if arg_name not in args_possible:
            invalid.append(arg_name)
    if not invalid:
        return True

    warning()
    for arg in invalid:
        message(f"- '[italic]--{arg}[/]' is not supported by any methods", color="yellow", end_warning=True)
    return False


################################################################################
# Method classes
################################################################################
def _validate_method_classes(configuration: Configuration, recipes: Recipes, method_classes: dict[str, TClass]) -> bool:
    """Find and run all 'validate' methods defined on our Method Classes."""
    messages = []
    for method, class_ in method_classes.items():
        instance = class_(configuration, recipes, {})  # Don't need "step" arg here..
        if validate_method := getattr(instance, "validate", None):
            if results := validate_method():
                messages.extend(results)

    if not messages:
        return True

    warning()
    for msg in messages:
        message(f"- {msg}", color="yellow", end_warning=True)
    return False


################################################################################
# Recipes themselves..
################################################################################
def _validate_recipes(recipes: Recipes, method_classes: dict[str, TClass]) -> bool:
    """Make sure all the the methods and steps from our recipes are defined and available."""
    if invalid_method_steps := __validate_steps(recipes, method_classes):
        failure()
        for method_step in invalid_method_steps:
            message(method_step, color="red", end_failure=True)
        return False
    return True


def __validate_steps(recipes: Recipes, method_classes_defined: dict[TClass]) -> list:
    """Each step in each recipe needs to be either a "built-in" method/class or refer to another valid step."""
    return_ = list()
    for id_, recipe in recipes:
        for step in recipe:
            if step.method:
                if step.method not in method_classes_defined:
                    return_.append(f"- Method: '{step.method}' in recipe={id_} is NOT a valid step method!")
            else:
                if recipes.get(step.recipe) is None:
                    return_.append(f"- Step: '{step.recipe}' in recipe={id_} can't be found in this file!")
    return return_


################################################################################
# Version number validation...
################################################################################
def _validate_existing_version_numbers(configuration: Configuration) -> bool:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml."""
    last_release_version = __get_last_release_from_readme()
    if last_release_version != configuration.version_:
        warning()
        message(
            f"- Warning, pyproject.toml has version: [italic]{configuration.version_}[/] "
            f"while last release in README is [italic]{last_release_version}[/]",
            color="yellow",
            end_warning=True,
        )
        return False
    return True


def __get_last_release_from_readme() -> [str, str]:
    """Mini state-machine to find last "release" in our changelog embedded within our README."""
    debug = False
    path_readme = Path.cwd() / "README.md"
    format_ = "markdown"
    if not path_readme.exists():
        path_readme = Path.cwd() / "README.org"
        format_ = "org"
        if not path_readme.exists():
            message(
                "Sorry, unable to open EITHER README.md or README.org from the current directory.",
                color="red",
                end_failure=True,
            )
            return path_readme, None

    if debug:
        msg = f"\nReading from {path_readme}"
        message(msg, color="light_slate_grey", end_success=True)

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
                msg = f"Found '{unreleased_header}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            continue
        if take_next_release and line.casefold().startswith(header):  # eg "*** vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            if debug:
                msg = f"Found next header matching '{line}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
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
                msg = f"Found '{unreleased_header}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            continue
        if take_next_release and line.startswith(header):  # eg "### vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            if debug:
                msg = f"Found next header matching '{line}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            return version
    return None
