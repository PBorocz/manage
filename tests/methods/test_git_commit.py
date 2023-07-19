"""Test git_commit method."""
from manage.models import Configuration, Recipes, Step
from manage.methods.git_commit import main as git_commit

COMMIT_MESSAGE = "A commit message"

def test_git_commit(git_repo):
    repo = git_repo.api

    # Setup: Stage a file in new/empty repository:
    file_path = git_repo.workspace / "commit.txt"
    file_path.write_text("Initial commit")
    repo.index.add([file_path])

    # Test
    step = Step(method="aMethod", confirm=False, quiet_mode=False, arguments=dict(message=COMMIT_MESSAGE))
    assert git_commit(Configuration(), Recipes.parse_obj({}), step, repo=repo)

    # Confirm: 1 - Did we get a commit?
    try:
        commits = list(repo.iter_commits())
        assert len(commits) == 1, "Sorry, we didn't find exactly 1 commit on our test repo."
    except ValueError:
        assert False, "Sorry, we didn't find anything committed to our test repo."

    # Confirm: 2 - Does it have the right message?
    assert commits[0].message == COMMIT_MESSAGE, "Sorry, we didn't find the right commit message on our commit"

    # Confirm: 3 - Does it have the right file?
    tree = commits[0].tree
    assert tree[0].name == file_path.name, f"Sorry, unable to find {file_path.name=} in commit."
