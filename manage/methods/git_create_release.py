"""Create github release."""
import os
from datetime import datetime

import requests

from manage.methods import AbstractMethod
from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, success


class Method(AbstractMethod):
    """Create github release."""
    def __init__(self, configuration: Configuration, recipes: Recipes, step: dict):
        """Create github release."""
        super().__init__(configuration, recipes, step)


    def run(self) -> bool:
        """Create github release."""
        now = datetime.now().strftime('%Y-%m-%dT%H%M')

        confirm = f"Ok to create github release using tag '[italic]{self.configuration.version}[/]'?"
        if not self.do_confirm(confirm):
            return False

        url = os.environ["GITHUB_API_RELEASES"]
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        auth = (os.environ["GITHUB_USER"], os.environ["GITHUB_API_TOKEN"])
        body = f"{self.configuration.version} | {now}. Details: {os.environ['GITHUB_PROJECT_RELEASE_HISTORY']}"
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
        return False
