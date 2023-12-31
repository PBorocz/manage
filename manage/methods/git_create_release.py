"""Create github release."""
import os
from datetime import datetime
from pathlib import Path
from pprint import pformat

import requests
from rich import print

from manage.methods import AbstractMethod
from manage.models import Configuration
from manage.utilities import failure, message, success


class Method(AbstractMethod):
    """Create github release using Github API."""

    def __init__(self, configuration: Configuration, step: dict):
        """Create github release."""
        super().__init__(__file__, configuration, step)

    def validate(self) -> None:
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
        if fails:
            self.exit_with_fails(fails)

    def run(self) -> bool:
        """Create github release."""
        now = datetime.now().strftime("%Y-%m-%dT%H%M")

        # Pull requisite Github configuration values
        url = os.environ["GITHUB_API_RELEASES"]
        user = os.environ["GITHUB_USER"]
        api_token = os.environ["GITHUB_API_TOKEN"]
        release_history = os.environ["GITHUB_PROJECT_RELEASE_HISTORY"]

        # Dry-run?
        if self.configuration.dry_run:
            self.dry_run(f"HTTPS:POST to github: name/release: '[italic]{self.configuration.version}[/]'")
            return True

        # Confirm?
        confirm = f"Ok to create github release with tag: '[italic]{self.configuration.version}[/]'?"
        if not self.do_confirm(confirm):
            return False

        # Do it!
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        auth = (user, api_token)
        body = f"{self.configuration.version} | {now}. Details: {release_history}"
        json = {
            "body": body,
            "draft": False,
            "name": self.configuration.version,
            "prerelease": False,
            "tag_name": self.configuration.version,
            "target_commitish": "trunk",
        }

        if self.step.verbose:
            message(f"Running [italic]{url}[/] Release: [italic]{self.configuration.version}[/]")

        response = requests.post(url, headers=headers, auth=auth, json=json)

        if response.status_code in (200, 201):
            if self.step.verbose:
                success()
            return True

        if self.step.verbose:
            failure()

        print(f"[red]≫ {pformat(response.json())}[/]")

        return False
