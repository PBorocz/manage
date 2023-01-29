from manage.steps.build import main as build
from manage.steps.check import main as check
from manage.steps.clean import main as clean
from manage.steps.git_commit_version_files import main as git_commit_version_files
from manage.steps.git_create_release import main as git_create_release
from manage.steps.git_create_tag import main as git_create_tag
from manage.steps.git_push_to_github import main as git_push_to_github
from manage.steps.poetry_bump_version_patch import main as poetry_bump_version_patch
from manage.steps.publish_to_pypi import main as publish_to_pypi
from manage.steps.run_pre_commit import main as run_pre_commit
from manage.steps.show import main as show
from manage.steps.update_readme import main as update_readme

__all__ = [
    build,
    check,
    clean,
    git_commit_version_files,
    git_create_release,
    git_create_tag,
    git_push_to_github,
    poetry_bump_version_patch,
    publish_to_pypi,
    run_pre_commit,
    show,
    update_readme,
]
