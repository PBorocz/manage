"""Create github release."""
import os
from datetime import datetime
from pathlib import Path
from pprint import pformat

import requests

from manage.methods import AbstractMethod
from manage.models import Configuration, PyProject
from manage.utilities import failure, message, msg_failure, success


class Method(AbstractMethod):
    """Create github release using Github API."""

    def __init__(self, configuration: Configuration, step: dict):
        """Create github release."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> list[str]:
        """Check to make sure we have the right credentials configured."""
        fails = []
        for env_var in [
            "GITHUB_API_RELEASES",
            "GITHUB_USER",
            "GITHUB_API_TOKEN",
            "GITHUB_PROJECT_RELEASE_HISTORY",
        ]:
            if env_var not in os.environ:
                msg = f"Can't find environment variable '[italic]{env_var}[/]' (required for {Path(__file__).stem})"
                fails.append(msg)
            # FIXME: Should we do anymore validation on some of these? like API_RELEASES should be a valid URL?
            # ...
        return fails

    def run(self) -> bool:
        """Create github release using the most up-to-date version in pyproject.toml."""
        now = datetime.now().strftime("%Y-%m-%dT%H%M")

        pyproject: PyProject = PyProject.factory()
        v_version = f"v{pyproject.version}"  # Use the vM.m.p format for the version here..

        # Dry-run?
        if self.configuration.dry_run:
            self.dry_run(f"HTTPS:POST to github: name/release: '[italic]{v_version}[/]'")
            return True

        # Confirm?
        confirm = f"Ok to create github release with tag: '[italic]{v_version}[/]'?"
        if not self.do_confirm(confirm):
            return False

        # Do it!
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        auth = (os.environ["GITHUB_USER"], os.environ["GITHUB_API_TOKEN"])
        body = f"{v_version} | {now}. Details: {os.environ['GITHUB_PROJECT_RELEASE_HISTORY']}"
        json = {
            "body": body,
            "draft": False,
            "name": v_version,
            "prerelease": False,
            "tag_name": v_version,
            "target_commitish": "trunk",
        }

        if self.step.verbose:
            message(f"Running [italic]{os.environ['GITHUB_API_RELEASES']}[/] Release: [italic]{v_version}[/]")

        response = requests.post(os.environ["GITHUB_API_RELEASES"], headers=headers, auth=auth, json=json)

        if response.status_code in (200, 201):
            if self.step.verbose:
                success()
            return True

        if self.step.verbose:
            failure()

        # Put out any error messages we received:
        msg_failure(f"≫ {pformat(response.json())}")

        return False
