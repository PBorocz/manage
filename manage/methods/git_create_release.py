import os
from datetime import datetime

import requests

from manage.models import Configuration, Recipes
from manage.utilities import ask_confirm, success


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Create github release"""
    now = datetime.now().strftime('%Y-%m-%dT%H%M')

    if step.confirm:
        if not ask_confirm(f"Ok to create github release using tag {configuration.version()}?"):
            return False

    url = os.environ["GITHUB_API_RELEASES"]
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    auth = (os.environ["GITHUB_USER"], os.environ["GITHUB_API_TOKEN"])
    body = f"{configuration.version()} | {now}. Details: {os.environ['GITHUB_PROJECT_RELEASE_HISTORY']}"
    json = {
        "body": body,
        "draft": False,
        "name": configuration.version(),
        "prerelease": False,
        "tag_name": configuration.version(),
        "target_commitish": "trunk",
    }
    response = requests.post(url, headers=headers, auth=auth, json=json)
    response.raise_for_status()
    success()
    return False
