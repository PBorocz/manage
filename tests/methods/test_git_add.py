"""Test git_add method."""
from manage.models import Configuration, Recipes, Step
from manage.methods.git_add import Method as git_add  # noqa: N813


def test_git_add(git_repo):
    repo = git_repo.api  # Repo itself is slightly buried..

    # Setup: Create an initial commit in our new/empty repository:
    file_path = git_repo.workspace / "commit_me.txt"
    file_path.write_text("Initial commit to get a 'HEAD' to diff against")
    repo.index.add([file_path])
    repo.index.commit("v1.0")
    assert len(list(repo.iter_commits())) == 1, "Sorry, unable to setup test repo with a single commit."

    # Setup: Create a file to be STAGED and the associated step to add it..
    file_path = git_repo.workspace / "stage_me.txt"
    file_path.write_text("A staged file's contents")
    step = Step(method="aMethod", confirm=False, verbose=True, arguments=dict(pathspec=str(file_path)))

    # Test
    assert git_add(Configuration(dry_run=False), Recipes.parse_obj({}), step).run(repo)

    # Confirm
    diff = repo.index.diff("HEAD")
    assert len(list(diff)) == 1, "Sorry, we didn't find anything staged by comparing against 'HEAD'."
    assert file_path.name == diff[0].a_path, f"Sorry, unable to find {file_path.name=} in list of staged files."
