"""Setup functions, not meant for direct calling from recipe file."""
import importlib
import sys
from pathlib import Path
from typing import Callable

from rich import print

from manage.models import Configuration, Recipes, PyProject, Recipe
from manage.utilities import message, success, failure


# def read_parse_recipes(path_to_recipes: Path) -> [dict, list]:
#     """Do the core TOML read of the user's specified Recipes file but don't convert into our object tree."""
#     raw_recipes = read_recipes_file(path_to_recipes)  # FIXME: Will sys.exit(1) if file not available!
#     return raw_recipes, parse_dynamic_arguments(raw_recipes)
#
# def parse_dynamic_argument(arg: str) -> [str, type]:
#     """Use the argument name to identify what type of argument we MIGHT expect.
#     Specifically:
#     "anArgument"  -> ["anArgument", str]
#     "an_argument" -> ["an_argument", str]
#     "aStrArg_str" -> ["aStrArg", str]
#     "another_int" -> ["another", int]
#     "yes_no_bool" -> ["yes_no", bool]
#     """
#     mapping = {"str": str, "int": int, "bool": bool}
#     pieces = arg.split("_")
#     if pieces[-1] in mapping:
#         type_ = mapping.get(pieces[-1])
#         return ["_".join(pieces[0:-1]), type_]
#     return [arg, str]
#
# def parse_dynamic_arguments(raw_recipes: dict) -> list[str, type]:
#     """Parse optional command-line arguments from the steps in this specific file."""
#     # Use a simple, *manual* parse of the recipe file provided!
#     arguments = dict()
#     errors = list()
#     for recipe_name, recipe in raw_recipes.items():
#         for step in recipe.get("steps", []):
#             for argument, value in step.get("arguments", {}).items():
#                 name_, type_ = parse_dynamic_argument(argument)
#                 if name_ in arguments:
#                     if type_ != arguments[name_][1]:
#                         errors.append(name_)
#                 else:
#                     arguments[name_] = (recipe_name, type_, value)
#     if errors:
#         print("[red]Sorry, the following arguments in your recipes file have inconsistent types, please correct!")
#         for error in errors:
#             print(f"[red]{error}")
#         sys.exit(1)

#     return list(arguments.items())


def uptype_recipes(
    configuration: Configuration,
    pyproject: PyProject,
    method_classes: dict[Callable] | None = None,
) -> Recipes:
    """We want a clean/easy-to-use recipe file, thus, do our own deserialisation and embellishment."""
    #
    # First, convert to strongly-typed dataclass instances
    #
    d_recipes = dict()
    for id_, raw_recipe in pyproject.recipes.items():
        recipe = Recipe(**raw_recipe)
        d_recipes[id_] = recipe
    recipes = Recipes.parse_obj(d_recipes)

    if method_classes:
        # Map the built-in classes available onto each recipe step.
        recipes = _add_classes(recipes, method_classes)

        # Validate that each of the methods provided are valid.
        # DEBUG! FIXME! While we're converting..
        # if not _validate_recipe_classes(configuration.verbose, recipes, method_classes):
        #     sys.exit(1)

    return recipes


def validate_existing_version_numbers(configuration: Configuration) -> bool:
    """Check that the last released version in README is consistent with canonical version in pyproject.toml."""
    if configuration.verbose:
        message("Checking consistency of versions (pyproject.toml & README)")
    last_release_version = __get_last_release_from_readme(configuration.verbose)
    if last_release_version != configuration.version_:
        failure()
        print(
            f"[red]Warning, pyproject.toml has version: {configuration.version_} "
            f"while last release in README is {last_release_version}!",
        )
        return False
    if configuration.verbose:
        success()
    return True


def __get_last_release_from_readme(verbose: bool) -> [str, str]:
    """Mini state-machine to find last "release" in our changelog embedded within our README."""
    path_readme = Path.cwd() / "README.md"
    format_ = "markdown"
    if not path_readme.exists():
        path_readme = Path.cwd() / "README.org"
        format_ = "org"
        if not path_readme.exists():
            print("[red]Sorry, unable to open EITHER README.md or README.org from the current directory.")
            return path_readme, None

    if verbose:
        msg = f"\nReading from {path_readme}"
        message(msg, color="light_slate_grey", end_success=True)
    method = __get_last_release_from_markdown if format_ == "markdown" else __get_last_release_from_org
    return method(verbose, path_readme)


def __get_last_release_from_org(verbose: bool, path_readme: Path) -> str:
    header = "***"
    unreleased_header = f"{header} Unreleased".casefold()
    take_next_release = False
    for i_line, line in enumerate(path_readme.read_text().split("\n")):
        if line.casefold().startswith(unreleased_header):
            take_next_release = True
            if verbose:
                msg = f"Found '{unreleased_header}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            continue
        if take_next_release and line.casefold().startswith(header):  # eg "*** vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            if verbose:
                msg = f"Found next header matching '{line}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            return version
    return None


def __get_last_release_from_markdown(verbose: bool, path_readme: Path) -> str:
    header = "###"
    unreleased_header = f"{header} Unreleased".casefold()
    take_next_release = False
    for i_line, line in enumerate(path_readme.read_text().split("\n")):
        if line.casefold().startswith(unreleased_header):
            take_next_release = True
            if verbose:
                msg = f"Found '{unreleased_header}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            continue
        if take_next_release and line.startswith(header):  # eg "### vX.Y.Z - <aDate>"
            tag = line.split()[1]
            version = tag[1:]
            if verbose:
                msg = f"Found next header matching '{line}' on line: {i_line+1}"
                message(msg, color="light_slate_grey", end_success=True)
            return version
    return None


def _validate_recipe_classes(verbose: bool, recipes: Recipes, method_classes: dict[str, Callable]) -> bool:
    """Make sure all the the methods and steps from our recipes are defined and available."""
    if verbose:
        message("Validating recipes")
    if invalid_method_steps := recipes.validate_method_steps(method_classes):
        print("\n[red]Sorry, we encountered the following errors in inbound recipe file:")
        for method_step in invalid_method_steps:
            print(f"[red]- {method_step}")
        failure()
        return False
    if verbose:
        success()
    return True


def _add_classes(recipes: Recipes, method_classes: dict[str, Callable]) -> Recipes:
    """Add the "callable" method onto each method step to dispatch on."""
    for name, recipe in recipes:
        for step in recipe:
            if class_ := method_classes.get(step.method):
                step.class_ = class_
    return recipes


# def _override_steps_from_args(recipes: Recipes, args) -> Recipes:
#     """Override any recipe settings with anything from the command-line."""
#     for name, recipe in recipes:
#         for step in recipe:
#             if args.no_confirm is True:  # Careful, default is None otherwise!
#                 # We ARE overriding confirm, is this a case where step.confirm is set?
#                 if step.confirm:
#                     step.confirm = False  # Yes..
#                     message(f"Overriding confirmation: {name} - {step.name()}", color='yellow')
#                     success(color="yellow")
#     return recipes


def gather_available_method_classes(verbose: bool) -> dict[str, Callable]:
    """Read and return all the python-defined step methods available."""

    def __gather_method_classes():
        """Iterate over all step modules (utility method)."""
        for path in sorted((Path(__file__).parent / Path("methods")).glob("*.py")):
            if path.name.startswith("__"):
                continue

            module = importlib.import_module(f"manage.methods.{path.stem}")

            # Convert methods like "_check_" and "_print" to "check" and "print"
            method_name = path.stem[1:] if path.stem.startswith("_") else path.stem

            yield method_name, getattr(module, "Method", None)

    # Get all the 'main" methods in each python file in the steps module:
    if verbose:
        message("Initialising methods available")

    classes = {method_name: cls for method_name, cls in __gather_method_classes()}
    if not classes:
        failure()
        print("[red]Unable to find [bold]any[/] valid method classes in manage/methods/*.py?")
        sys.exit(1)

    if verbose:
        success()
    return classes
