# Available Methods

| Method Name                                                         | Confirmation? | Arguments? | Arguments           |
|---------------------------------------------------------------------|---------------|------------|---------------------|
| [`clean`](#clean)                                                   | Yes           | \-         |                     |
| [`command`](#command)                                               | Yes           | Required   | `command`           |
| [`git_add`](#git_add)                                               | Yes           | Optional   | `pathspec`          |
| [`git_commit_version_files`](#git_commit_version_files)             | Yes           | \-         |                     |
| [`git_commit`](#git_commit)                                         | Yes           | Optional   | `message`           |
| [`git_create_release`](#git_create_release)                         | Yes           | \-         |                     |
| [`git_create_tag`](#git_create_tag)                                 | Yes           | \-         |                     |
| [`git_push_to_github`](#git_push_to_github)                         | Yes           | \-         |                     |
| [`pandoc_convert_org_to_markdown`](#pandoc_convert_org_to_markdown) | Yes           | Required   | `path_md, path_org` |
| [`poetry_build`](#poetry_build)                                     | Yes           | \-         |                     |
| [`poetry_lock_check`](#poetry_lock_check)                           | No            | \-         |                     |
| [`poetry_publish`](#poetry_publish)                                 | Yes           | \-         |                     |
| [`poetry_version_sync`](#poetry_version_sync)                       | Yes           | Required   | `init_path`         |
| [`poetry_version`](#poetry_version)                                 | Yes           | Required   | `poetry_version`    |
| [`pre_commit`](#precommit)                                          | No            | \-         |                     |
| [`sass`](#sass)                                                     | Yes           | Required   | `pathspec`          |
| [`update_readme`](#update_readme)                                   | Yes           | Optional   | `readme`            |

## Common Method Options

- `confirm`: Ask for confirmation before executing the respective step, e.g. "Are you sure you want to ...?". Primarily on behalf of *write*-oriented steps, this option can be specified either on a step-by-step basis:

``` toml
[[tool.manage.recipes."1_bump".steps]]
method = "poetry_version"
confirm = true
arguments = { poetry_version = "patch" }

```

or directly on the command-line:

``` shell
% manage commit_and_release --confirm --live
```

- `allow_error`: If True, a non-zero exit code will stop execution of the respective recipe (default is False). This useful for particular commands where it's both possible and expected that an error is returned (for example, clearing our temporary files). For example:

``` toml
[[tool.manage.recipes.build.steps]]
method = "clean"
confirm = false
allow_error = true
```

## Method Details
### **clean**

- Method to delete build artifacts, ie. `rm -rf build \*.egg-info`.
- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "clean"
allow_errors = false
confirm = false
...
```

### **command**

- General method to run essentially any local command for it's respective side-effects. 

- For example, in one of my projects, I don't use the version number in `pyproject.toml` but instead in an `app/version.py` that is updated from a small script (using the date & respective branch of the last git commit performed).

- This command **may** ask for confirmation depending on the `confirm` flag.

```toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "command"
allow_error = false
arguments = {command: "./app/cli/update_settings.py"}
...
```

#### Arguments
* `command` Required, a string containing the full shell command to execute.

### **git_add**

- Method to perform a `git add <pathspec>` operation.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "git_add"
confirm = true
arguments = { pathspec = "README.md pyproject.toml" }
...
```

#### Arguments
- `pathspec` Optional path specification of dir(s) and/or file(s) to stage. Default if not specified is `.`.

### **git_commit_version_files**

- Specialised method (really a customised version of `git_commit`) to `git stage` and `git commit` two files relevant to the build process: `pyproject.toml` and `README.(org|md)`.

- Specifically, other methods will update these files for version management and this method is provided to get them into git on behalf of a release. Alternately, you can use the more general `git_commit` method, specifying these two files to be added.

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "git_commit_version_files"
confirm = true
```

### **git_commit**

- Method to perform a `git commit <pathspec>` operation.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "git_commit"
confirm = true

[[tool.manage.recipes.<aRecipeName>.steps.arguments]]
pathspec = "README.md pyproject.toml"
message ="Auto-commit"}
...
```

#### Arguments
* `pathspec` Optional path specification of dir(s) and/or file(s) to commit. Default if not specified is `.`.
* `message` Optional commit message. Default if not specified is today's date (in format: ~yyyymmddThhmm~).

### **git_create_release**

- Method to create a git **release** using the appropriate version string (from `pyproject.toml`). This method uses the GitHub API so the environment variables listed above are required to use this method.

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "git_create_release"
```

### **git_create_tag**

- Method to create a local git **tag** using the appropriate version string (from the potentially updated `pyproject.toml`), e.g. `git tag -a <version> -m <version>`

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "git_create_release"
```

### **git_push_to_github**

- Method command to perform a `git push --follow-tags`.

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "git_push_to_github"
```

### **pandoc_convert_org_to_markdown**

- Specialised method to convert an emacs .org file to a markdown (.md) file using pandoc; specifically:

```shell
pandoc -f org -t markdown --wrap none --output <path_md> <path_org>
```

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "pandoc_convert_org_to_markdown"
confirm = true

[[tool.manage.recipes.<aRecipeName>.steps.arguments]]
path_md = "./docs/my_doc.md"
path_org ="./docs/my_doc.org"
...
```

#### Arguments
* `path_md` Required, path specification input markdown file, e.g. `./docs/my_doc.md`.
* `path_org` Required, path specification resulting .org file to be created, e.g. `./docs/my_doc.org`.

### **poetry_build**

- Method to "poetry" build a package distribution, ie. `poetry build`.
- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.
- A complete example of this might be:

``` toml
[tool.manage.recipes.build]
description = "Build our distribution(s)"

[[tool.manage.recipes.build.steps]]
method = "poetry_lock_check"
confirm = false

[[tool.manage.recipes.build.steps]]
recipe = "clean"
confirm = false

[[tool.manage.recipes.build.steps]]
method = "poetry_build"
confirm = false
```

### **poetry_lock_check**

- Method to perform a poetry lock "check" to verify that `poetry.lock` is consistent with `pyproject.toml`. If it isn't, will update/refresh `poetry.lock` (after confirmation).

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "poetry_lock_check"
allow_errors = false
...
```

### **poetry_publish**

- Method to publish your package to PyPI, e.g. `poetry publish`.

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "poetry_publish"
allow_errors = false
```

### **poetry_version_sync**

- Specialised method to update your `__init__.py`'s file's `__version__ = "version"` line to the most current version in pyproject.toml.
- This is commonly used *after* `poetry_version` has updated a version number AND when you want to use this common pattern (without resorting to importlib.metadata): `import myPackage; print(myPackage.__version__)`

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "poetry_version_sync"
arguments = {bump_rule: "patch"}
...
```

``` shell
% manage aRecipeName --live --poetry_version_sync:init_path "manage/__init__.py"
```
#### Arguments
* `init_path` Required, path to the specific .py file that contains your __version__ line (usually, this is in your package's (not your project's) top-level directory.

### **poetry_version**

- Specialised method to "bump" the version of a project/package using Poetry's version command. Takes one of three pre-defined version levels to bump and updates `pyproject.toml` with the new version value.
- A common use of this method is to provide an command-line override for the `bump_rule` to from having to edit the `pyproject.toml` file.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "poetry_version"
arguments = {bump_rule: "patch"}
...
```

``` shell
% manage aRecipeName --live --poetry_version:bump_rule minor
```
#### Arguments
* `bump_rule` Required, the default level of version "bump" to perform. Must be one of 'patch', 'minor', 'major', 'prepatch', 'preminor', 'premajor', 'prerelease' (see [Poetry version command](https://python-poetry.org/docs/cli/#version) for more information).


### **precommit**

- Method to run the `pre-commit` tool (if you use it), e.g. `pre-commit run --all-files`

- This command takes **no** arguments but **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "precommit"
allow_error = true
...
```

### **sass**

- Method to run a `sass` command to convert scss to css, e.g. `sass <pathSpec>`

``` toml
...
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "sass"
allow_error = false
arguments = {pathspec: "./app/static/css/sass/mystyles.scss ./app/static/css/mystyles.css"}
...
```
#### Arguments
* `pathspec` Required path specification of dir(s) and/or file(s) to run.

### **update_readme**

- Specialised method to move "Unreleased" items into a dedicated release section of a README file.

- README file can be in either [Org](https://orgmode.org/) or Markdown format, ie. `README.md` or `README.org`.

- We assume `README.org/md` is in the same directory as your `pyproject.toml` and `manage.yaml`. This is almost always the root directory of your project.

- This command **may** ask for confirmation depending on the `confirm` flag.

``` toml
...
# Will look for either README.org or README.md!
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "update_readme"
allow_error = false
...
```

``` toml
...
# With optional argument:
[[tool.manage.recipes.<aRecipeName>.steps]]
method = "update_readme"
allow_error = false
arguments = {readme: "./subDir/README.txt"}
...
```

#### Arguments
 * `readme` Optional, a string that represents a full path to your respective README.\* file. If not specified, we search for `./README.org` and `./README.md` in the same directory as your `pyproject.toml`.

