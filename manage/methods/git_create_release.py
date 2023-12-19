"""Create github release."""
import os
import sys
from datetime import datetime

import requests

from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import message, success


class Method(AbstractMethod):
    """Create github release using Github API."""

    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Create github release."""
        super().__init__(configuration, recipes, step)

    def run(self) -> bool:
        """Create github release."""
        now = datetime.now().strftime("%Y-%m-%dT%H%M")

        # Pull requisite Github configuration values
        # FIXME: Can these be in "setup check" instead of here?
        if not (url := os.environ["GITHUB_API_RELEASES"]):
            message("Sorry, unable to find environment variable '[italic]GITHUB_API_RELEASES[/]'", color="red")
            sys.exit(1)

        if not (user := os.environ["GITHUB_USER"]):
            message("Sorry, unable to find environment variable '[italic]GITHUB_USER[/]'", color="red")
            sys.exit(1)

        if not (api_token := os.environ["GITHUB_API_TOKEN"]):
            message("Sorry, unable to find environment variable '[italic]GITHUB_API_TOKEN[/]'", color="red")
            sys.exit(1)

        if not (release_history := os.environ["GITHUB_PROJECT_RELEASE_HISTORY"]):
            message(
                "Sorry, unable to find environment variable '[italic]GITHUB_PROJECT_RELEASE_HISTORY[/]'",
                color="red",
            )
            sys.exit(1)

        # Dry-run?
        if self.configuration.dry_run:
            self.dry_run("HTTPS:POST to github: name/release: '[italic]{self.configuration.version}[/]'")
            return True

        # Confirm
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
        response = requests.post(url, headers=headers, auth=auth, json=json)
        response.raise_for_status()
        success()
        return True
