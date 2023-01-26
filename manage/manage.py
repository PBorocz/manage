"""'Manage' environment."""
import argparse
import os
import shlex
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import yaml
from tomli import load
from dotenv import load_dotenv

try:
    from rich import print
    from rich.console import Console
    input = Console().input
    HAVE_RICH = True
except ImportError:
    HAVE_RICH = False

load_dotenv(verbose=True)

UNRELEASED_HEADER = "*** Unreleased"
PATH_README = Path.cwd() / "README.org"

VERSION = None  # Will be set to current value on startup and *may* be changed as part of processing.


################################################################################
# Utility methods, not meant for direct calling from manage.yaml.
################################################################################
def _color(color: str) -> Optional[str]:
    """Utility method to either return a markup color if possible or skip colors entirely."""
    if HAVE_RICH:
        return f"[{color}]"
    return ""


def _ask_confirm(text: str) -> bool:
    """Ask for confirmation, returns True if "yes" answer, False otherwise"""
    while True:
        answer = input(f"\n{_color('#fffc00')}{text} (y/N) >").lower()
        if answer in ("n", "no", ""):
            return False
        elif answer in ("y", "yes"):
            return True


def __flag(char: str, msg: Optional[str]) -> None:
    """Create and print a success or failure with optional message."""
    out_ = char if not msg else f"{char} {msg}"
    print(out_)


def _success(msg: Optional[str] = None) -> None:
    """Render/print a success message."""
    __flag(f"{_color('green')}✔", msg)


def _failure(msg: Optional[str] = None) -> None:
    """Render/print a failure message."""
    __flag(f"{_color('red')}✖", msg)


def _fmt(message: str, overhead: int = 0, color: str = 'blue') -> str:
    """Pad the message string to width (net of overhead) and in the specified color (if possible)."""
    padding = 60 - overhead - len(message)
    return f"{_color(color)}{message}{'.' * padding}"


def _run(step: Optional[dict], command: str) -> tuple[bool, str]:
    """Run the command for the specified (albeit optional) step, capturing output and signalling success/failure."""
    msg = _fmt(f"Running [italic]{command}[/italic]", overhead=-17)
    print(msg, flush=True, end="")

    result = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        # Command failed, are we allowed to have errors?
        if step and not step.get("allow_error", False):
            _failure(result.stderr.decode())
            return False, result.stderr.decode()
    # Command succeeded Ok.
    if step and step.get("echo_stdout", False):
        _success(result.stdout.decode().strip())
    else:
        _success()

    return True, result.stdout.decode().strip()


def _get_package_from_pyproject() -> Optional[str]:
    """Read the pyproject.toml file to return the name of the current package we're working with."""
    msg = _fmt("Getting package from pyproject.toml", color='blue')
    print(msg, end="", flush=True)
    with open(Path("./pyproject.toml"), "rb") as fh_:
        pyproject = load(fh_)
    if packages := pyproject.get("tool", {}).get("poetry", {}).get("packages", None):
        try:
            # FIXME: For now, we support the first entry in tool.poetry.packages
            #        (even though multiple are allowed)
            package_include = packages[0]
            package = package_include.get("include")
            _success()
            return package
        except IndexError:
            ...
    _failure()
    return None


def _read_configuration() -> dict:
    msg = _fmt("Reading configuration from manage.yaml", color='blue')
    print(msg, flush=True, end="")
    with open("manage.yaml", 'r') as stream:
        configuration = yaml.safe_load(stream)
    _success()

    # Make sure all the the methods and steps are defined and available:
    msg = _fmt("Checking configuration", color='blue')
    print(msg, flush=True, end="")
    invalid_method_references = list()
    invalid_step_references = list()
    for target in sorted(list(configuration.keys())):
        for step in configuration.get(target).get("steps"):
            if "step" in step:
                step_name = step.get("step")
                if step_name not in configuration:
                    invalid_step_references.append(step_name)
            elif "method" in step:
                method_name = step.get("method")
                if method_name not in globals():
                    invalid_method_references.append(method_name)

    if invalid_method_references or invalid_step_references:
        if invalid_method_references:
            print("\nSorry, error in manage.yaml; The following method(s) can't be found:")
            for method_name in invalid_method_references:
                print(f"- {method_name}")
        if invalid_step_references:
            print("\nSorry, error in manage.yaml; The following step(s) can't be found:")
            for step_name in invalid_step_references:
                print(f"- {step_name}")
        _failure()
        return None

    _success()
    return configuration


################################################################################
# Pre-defined step methods
# Each of which is an atomic operation that may or may not require confirmation.
################################################################################
def poetry_bump_version_patch(step) -> bool:
    """Use poetry to do a "patch" level version bump to pyproject.toml"""
    # FIXME Can we parse pyproject.toml to find the "packages" line to find the name of our project
    # instead of hard-coding it below?
    global VERSION

    # Use poetry to get what our next version would be:
    success, result = _run(step, "poetry version patch --dry-run")
    if not success:
        print(f"Sorry, Poetry couldn't determine a new version number from pyproject.toml: {result}")
        sys.exit(1)
    _, version = result.split()  # a bit fragile, we're relying on poetry default message format :-(

    ################################################################################
    # Safety check
    ################################################################################
    if step.get("confirm", False):
        if not _ask_confirm(f"Ok to bump version from v{VERSION} to v{version} in pyproject.toml?"):
            return False

    # Update our version in pyproject.toml
    _, result = _run(step, "poetry version patch")
    _, VERSION = result.split()
    assert version == VERSION
    return True


def update_readme(step) -> bool:
    """Search for 'Unreleased...' header in Changelog portion of README and replace with current version and date."""
    if step.get("confirm", False):
        msg = f"Ok to update README.org's 'Unreleased' header to v{VERSION}?"
        if not _ask_confirm(msg):
            print("OK. Nothing done (but pyproject.toml may still be on new version)")
            return False

    # Read and update the Changelog section embedded our README.org with the
    # new version (leaving another "Unreleased" header for future work)
    readme = PATH_README.read_text()
    if UNRELEASED_HEADER not in readme:
        _failure(f"Sorry, couldn't find a header consisting of '{UNRELEASED_HEADER}' in README.org!")
        return False

    msg = _fmt("Running update to README.org: '{UNRELEASED_HEADER}'", color='blue')
    print(msg, flush=True, end="")
    header_release = f"*** v{VERSION} - {datetime.now().strftime('%Y-%m-%d')}"
    readme = readme.replace(UNRELEASED_HEADER, UNRELEASED_HEADER + "\n" + header_release)
    PATH_README.write_text(readme)
    _success()
    return True


def git_commit_version_files(step) -> bool:
    """Commits updated files that contain version information locally."""
    msg = "Ok to commit changes to pyproject.toml and README.org?"
    if step.get("confirm", False):
        if not _ask_confirm(msg):
            print(f"OK. To rollback, you may have to set version back to {VERSION} re-commit locally.")
            return False
    if not _run(step, "git add pyproject.toml README.org")[0]:
        return False
    if not _run(step, f'git commit --message "Bump version to v{VERSION}"')[0]:
        return False
    return True


def clean(step) -> bool:
    """Clean the build environment"""
    if step.get("confirm", False):
        if not _ask_confirm("Ok to clean build environment?"):
            return False
    return _run(step, "rm -rf build dist *.egg-info")[0]


def build(step) -> bool:
    """Build the distribution"""
    if step.get("confirm", False):
        if not _ask_confirm("Ok to build distribution files?"):
            return False
    return _run(step, "poetry build")[0]


def run_pre_commit(step) -> bool:
    if step.get("confirm", False):
        if not _ask_confirm("Ok to run pre-commit?"):
            return False
    return _run(step, "pre-commit run --all-files")[0]


def git_create_tag(step) -> bool:
    """Create git tag, i.e. v<major>.<minor>.<patch>"""
    tag = f"v{VERSION}"
    if step.get("confirm", False):
        if not _ask_confirm(f"Ok to create tag: {tag}?"):
            return False
    return _run(step, f"git tag -a {tag} --message {tag}")[0]


def git_push_to_github(step: dict) -> bool:
    """Push to github"""
    if step.get("confirm", False):
        if not _ask_confirm("Ok to push to github?"):
            return False
    return _run(step, "git push --follow-tags")[0]


def publish_to_pypi(step: dict) -> bool:
    """Have poetry push/publish/upload to pypi"""
    if step.get("confirm", False):
        if not _ask_confirm("Ok to publish to PyPI?"):
            return False
    return _run(step, "poetry publish")[0]


def git_create_release(step: dict) -> bool:
    """Create github release"""
    now = datetime.now().strftime('%Y-%m-%dT%H%M')

    # Extract changes from changelog for this version...
    tag = f"v{VERSION}"

    if step.get("confirm", False):
        if not _ask_confirm(f"Ok to create github release using tag {tag}?"):
            return False

    url = os.environ["GITHUB_API_RELEASES"]
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    auth = (os.environ["GITHUB_USER"], os.environ["GITHUB_API_TOKEN"])
    body = f"{tag} | {now}. Details: {os.environ['GITHUB_PROJECT_RELEASE_HISTORY']}"
    json = {
        "body": body,
        "draft": False,
        "name": tag,
        "prerelease": False,
        "tag_name": tag,
        "target_commitish": "trunk",
    }
    response = requests.post(url, headers=headers, auth=auth, json=json)
    response.raise_for_status()
    _success()
    return False


################################################################################
# Primary control methods
################################################################################
def _dispatch(package: str, configuration: dict, target: str) -> None:
    """Iterate (ie. execute) each step in the selected target's configuration for the specified package."""

    for step in configuration.get(target).get("steps"):
        assert "step" in step or "method" in step, f"Sorry, one of '{target}'s steps is missing 'step' or 'method'."

        # This step could be either a request to invoke a particular method OR a request to run another step
        if "step" in step:
            # Run another step
            _dispatch(step.get("step"), configuration)

        elif "method" in step:
            # Lookup and run the method associated with the step:
            method = globals().get(step.get("method"))
            method(step)


def main():
    """Requisite docstring."""

    # Confirm we're working from the README/root level of our project
    if not PATH_README.exists():
        print("Sorry, we need run this from the same direction that your README.org file sits.")
        sys.exit(1)

    # Read configuration and package we're working on
    packge = _get_package_from_pyproject()
    if packge is None:
        sys.exit(1)

    config = _read_configuration()
    if config is None:
        sys.exit(1)

    # Handle arg(s)
    targets_available = ', '.join(list(config.keys()))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target",
        type=str,
        help=f"Please specify a target to run from: {targets_available}",
        nargs="?",
        default=None
    )
    args = parser.parse_args()
    if not vars(args) or not args.target:
        parser.print_help()
        sys.exit(0)

    # Validate requested target
    if args.target.casefold() not in config:
        print(f"Sorry, {args.target} is not a valid target, please check against manage.yaml.")
        sys.exit(1)

    # Although we might update it as part of our steps, in case we don't, get the current value as of now
    global VERSION
    _, VERSION = _run(None, "poetry version --short")

    try:
        _dispatch(packge, config, args.target)
        print(f"\n{_color('green')}Done!")
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)


if __name__ == "__main__":
    main()


################################################################################
# ARCHIVED (they work but are not needed)
################################################################################
# def _get_changes_from_readme(version: str) -> str:
#     """Mini state-machine to find the changelog lines associated with the version specified."""
#     _running(f"Running query of README.org for changes obo {VERSION}")
#     in_version = False
#     changes = list()
#     for line in PATH_README.read_text().split("\n"):
#         if version in line:
#             in_version = True  # Found the right line, after which are our changes..
#             continue
#         if in_version:
#             if line.startswith("***"):
#                 break  # We're done...we hit the next header line..
#             changes.append(line.strip())
#     if changes:
#         _success(f"({len(changes)} entries found)")
#     else:
#         _failure()
#     return changes
