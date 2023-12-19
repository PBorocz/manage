"""Test git_commit method."""
from manage.models import Configuration, Recipes, Step
from manage.methods.git_commit import Method as git_commit  # noqa: N813

COMMIT_MESSAGE = "A commit message"


def test_git_commit(git_repo):
    # Setup: Stage a file in new/empty repository:
    file_path = git_repo.workspace / "commit.txt"
    file_path.write_text("Initial commit")
    git_repo.api.index.add([file_path])

    # Test!
    step = Step(method="aMethod", confirm=False, verbose=True, arguments=dict(message=COMMIT_MESSAGE))
    assert git_commit(Configuration(dry_run=False), Recipes.parse_obj({}), step).run(git_repo.api)

    # Confirm: 1 - Did we get a commit?
    try:
        commit = git_repo.api.head.commit
    except ValueError:
        assert False, "Sorry, we didn't find anything committed to our test repo."

    # Confirm: 2 - Was it only of a single file?
    assert commit.stats.total.get("files") == 1

    # Confirm: 3 - Was it the *right* file?
    for file, diff in commit.stats.files.items():
        assert file == file_path.name, f"Sorry, unable to find {file_path.name=} in commit.stats!"

    # Confirm: 4 - Does it have the right message?
    assert commit.message == COMMIT_MESSAGE, "Sorry, we didn't find the right commit message on our commit"
