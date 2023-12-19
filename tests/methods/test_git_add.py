"""Test git_add method."""
from manage.models import Configuration, Recipes, Step
from manage.methods.git_add import Method as git_add  # noqa: N813


def test_git_add(git_repo):
    # Setup: Create an initial commit in our new/empty repository:
    path = git_repo.workspace / "commit_me.txt"
    path.write_text("Initial commit to get a 'HEAD' to diff against")
    git_repo.api.index.add([path])
    git_repo.api.index.commit("v1.0")
    assert len(list(git_repo.api.iter_commits())) == 1, "Sorry, unable to setup test repo with a single commit."

    # Setup: Create a file to be STAGED and the associated step to add it..
    path = git_repo.workspace / "stage_me.txt"
    path.write_text("A staged file's contents")

    step = Step(method="testGitAdd", confirm=False, verbose=True, arguments=dict(pathspec=str(path)))

    # Test
    assert git_add(Configuration(dry_run=False, confirm=False), Recipes.parse_obj({}), step).run(git_repo.api)

    # Confirm
    diff = git_repo.api.index.diff("HEAD")
    assert len(list(diff)) == 1, "Sorry, we didn't find anything staged by comparing against 'HEAD'."
    assert path.name == diff[0].a_path, f"Sorry, unable to find {path.name=} in list of staged files."
