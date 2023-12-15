# Manage

## Introduction

In learning how to perform releases to PyPI, I became somewhat "disenchanted" by all the various manual steps and required.

In the spirit of GTD, a Makefile (or personal favorite [Justfile](https://github.com/casey/just)) was a good starting point.

However, even these left something to be desired which led me to [Thomas Feldman\'s manage.py](https://github.com/tfeldmann/organize/blob/main/manage.py) environment. I wanted to combine the best of Justfile's and Thomas' environment through a stand-alone package that I could easily apply to my myriad python projects (irrespective of whether they're released as formal packages).

Thus, this package automates all the common operations for [Poetry](https://python-poetry.org/) & README-based project/package management that I perform on a day-to-day basis. In particular, those that I don't perform regularly and/or require multiple steps to perform (and thus, tend to forget how to do!)

Here's an example of building and releasing a python package:

![Sample Session](Screenshot.png)

## Design

- Every granular command that might need to be performed on behalf of project/package management is packaged as a `method` (eg. poetry build, git commit etc.)

- These granular methods are combined into `recipes` to perform a particular task (eg. build my project, update my release notes etc.)

- Recipes are stored in a local recipe file (default `./manage.yaml`) that is _specific to your project_.

- Recipes can be _nested_ (analogous to cooking recipes where one recipe may refer to another for a component).

- A recipe file (or `manage.yaml` file) contains:

    - A set of *targets* aka recipes (terminology synonymous with Makefile/Justfile targets).

    - Each target consists of a set of steps, each of which is shorthand description of what needs to be accomplished.

    - Each step can refer either to a built-in **method** (e.g. `clean`) or to the name of another *recipe*.

- Each step in a target is also described by the following:

    - Steps that have a side-effect (ie. those that can *change* something) can have a user-confirmation before executing, eg. "Are you sure? (`confirm`).

    - Each step can be configured as to whether or not it\'s stdout is displayed (`echo_stdout`).

    - Each step can be configured control whether errors encountered are fatal or not (`allow_error`).

### Example

An example `manage.yaml` might look like this:

``` yaml
################################################################################
bump:
  description: Bump the version number to the next /patch/ level and commit locally
  steps:
    - method: poetry_bump_version
    - method: update_readme
    - method: git_commit_version_files

################################################################################
clean:
  description: Clean out our temp files and ALL previous builds.
  steps:
    - method: clean
      echo_stdout: false                # Run quietly

################################################################################
build:
  description: Build our distribution(s).
  steps:
    - method: build
      confirm: false                    # Ok to build without confirmation
      echo_stdout: true                 # We want to see the output of our build!
      allow_error: true                 # We don't care if no files are clean or if dirs don't exist.
```

## Assumptions

These are my common python project standards, allowing for the ability of this tool to work seamlessly. To the degree that your development/project/release environment strays from mine, the tool probably becomes less relevant.

### Tools

- We assume [Git/Github](https://github.com) are used for code version management.
- We assume [poetry](https://python-poetry.org) is used to manage package dependencies **and** build environment.
- We assume that execution of this script is from the TOP level of a project, i.e. at the same level as pyproject.toml.
- We assume that **version string** in `pyproject.toml` is the SINGLE and CANONICAL version string in our project/package. Specifically, there are no `/module/__version__.py`\'s or versions embedded in `__init__.py~` files (Should you want/need to have these, it\'s certainly possible to automate the creation of them based on the version from `pyproject.toml`!).

### Versioning

- We assume semantic versioning with `poetry version` to update/manage our version number. Specifically, this allows us to use `poetry version` command\'s keywords for version updates, ie. patch, minor, major etc.

### CHANGELOG/Release History Management

- We do **not** use a stand-alone `CHANGELOG` file, instead we use a specific section in `README.org/md`. We assume that list of completed but unreleased items exist under an "**Unreleased**" header. This format provides reasonably clean automation of version/release management within the README file.

### Configuration

- We assume the following GitHub entries are available in our environment (either set in your respective shell or through .env):

| Environment Variable               | Explanation            | Example
| ---------------------------------- | ---------------------- | --------------------------------------------------------------------------------
| `GITHUB_USER`                      | User id                | `John-Jacob_JingleheimerSchmidt`
| `GITHUB_API_TOKEN`                 | Personal API token     | `ghp_1234567890ABCDEFG1234567890`
| `GITHUB_API_RELEASES`              | URL to release API     | `https://api.github.com/repos/><user>/<project>/releases`
| `GITHUB_PROJECT_RELEASE_HISTORY`   | URL to release history | `https://github.com/<user>/<project>/blob/trunk/README.org#release-history`

Note: technically, we might be able to infer `GITHUB_PROJECT_RELEASE_HISTORY` based on the `GITHUB_USER` and project name but I think we'd have to infer the name of the "mainline" branch, some have moved `master` to `main` and others to `trunk`.

## Installation

This isn't packaged for PyPI. However, distribution files are released to github.

If you use `poetry`, this should suffice (and is how I use it from my projects). Specifically, we're installing the package's from it's github repository directly into our environment.

``` shell
% poetry add git+https://github.com/PBorocz/manage --group dev
```

Create your `manage.yaml` file, here's a sample one to start from:

``` yaml
clean:
  description: Clean out our temp files and ALL previous builds.
  steps:
    - method: clean
      echo_stdout: true

build:
  description: Build our package.
  steps:
    - step: clean
    - method: build
      confirm: true
      echo_stdout: true
```

At this point, you should be able to run: `manage check` (one of the built-in targets) against `manage.yaml` you just created. Note that `poetry add` will create a `manage` command into your respective python /bin environment (hopefully, your virtual env).

## Documentation
*NB: This section is **big** and should probably be moved to stand-alone documentation!*

### Command-Line Arguments

1.  -r/--recipe

    Use another recipe file instead of the default `./manage.yaml`.

2.  --confirm

    Override any `confirm: False` entries in your recipe.file and force all methods with confirmation (ie. state-change) to do so.

3.  --noconfirm

    Override any `confirm: True` entries in your recipe.file and force all confirmation methods to **NOT** require (ie. skip) confirmation.

4.  --verbose

    Provide an extra-level of output regarding method execution (for example, including a method command's stdout stream if available)

### Default Recipe Targets

The following recipes are built-in and available irrespective of your recipe file:

- `check` - Performs a validity check of your recipe file (ie. `manage.yaml`). For example:

    ``` shell
    % python manage check
    Reading recipes (manage.yaml)..................................................✔
    Reading package & version (pyproject.toml).....................................✔
    Checking consistency of versions (pyproject.toml & README).....................✔
    Reading recipe steps available.................................................✔
    Validating recipes.............................................................✔
    %
    ```

- `print` - Does a "pretty-print" of your respective recipe file. For example:

    ``` shell
    % python manage print
    Recipes(
        __root__={
            'bump': Recipe(
                description='Bump the version number to the next /patch/ level and commit locally',
                steps=[
                    Step(
                        method='poetry_bump_version',
                        recipe=None,
                        confirm=True,
                        echo_stdout=False,
                        allow_error=False,
                        quiet_mode=False,
                        arguments={'poetry_version': 'patch'},
                        callable_=<function main at 0x1084e1990>
                    ),
                    Step(
                        method='update_readme',
                        recipe=None,
                        confirm=True,
                        echo_stdout=False,
                        allow_error=False,
                        quiet_mode=False,
                        arguments={'readme_format': 'org'},
                        callable_=<function main at 0x1084e20e0>
                    ),
                    Step(
                        method='git_commit_version_files',
                        recipe=None,
                        confirm=True,
                        echo_stdout=False,
                        allow_error=False,
                        quiet_mode=False,
                        arguments={},
                        callable_=<function main at 0x10805beb0>
                    )
                ]
            ),
            'build': Recipe(
                description='Build our distribution(s) and release to "github" (not PyPI!)',
                steps=[
                    Step(
                        method='poetry_lock_check',
                        recipe=None,
                        confirm=False,
                        echo_stdout=False,
                        allow_error=False,
                        quiet_mode=False,
                        arguments={},
                        callable_=<function main at 0x1084e1ab0>
                    ),
                    .....
    %
    ```

### Common Method Options

- `confirm` - Ask for confirmation before executing the respective step, e.g. "Are you sure you want to ...?". Primarily on behalf of *write*-oriented steps, this option can be specified either on a step-by-step basis:

    ``` yaml
    build_my_package:
      description: Build my distribution package.
      steps:
        - method: build
          confirm: True
    ```

    **or** for all confirm-able steps during a specific execution from the command-line (which will override any step-specific settings):

    ``` shell
    % python manage my_recipe --confirm
    ...
    %
    ```

- `echo_stdout` - Echo the stdout of the respective command.

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...
    - method: git_create_tag
      echo_stdout: True
    - method: ...
      ...
```

- `allow_error` - If True, a non-zero exit code will stop execution of the respective recipe (default is False).

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: clean
      allow_error: True
    - method: ...
      ...
```

### Available Methods
#### Summary

We provide a summary of the methods supported (listed alphabetically):

| Method Name                      | Confirmation? | Arguments? | Arguments
|----------------------------------|---------------|------------|-------------
| `build`                          | Yes           | \-         |
| `clean`                          | Yes           | \-         |
| `git_add`                        | Yes           | Optional   | `pathspec`
| `git_commit`                     | Yes           | Optional   | `pathspec, message`
| `git_commitversionfiles`         | No            | \-         |
| `git_create_release`             | Yes           | \-         |
| `git_create_tag`                 | Yes           | \-         |
| `git_push_to_github`             | Yes           | \-         |
| `pandoc_convert_org_to_markdown` | No            | Required   | `path_md, path_org`
| `poetry_bump_version`            | Yes           | Required   | `poetry_version`
| `poetry_lock_check`              | No            | \-         |
| `publish_to_pypi`                | Yes           | \-         |
| `run_command`                    | Yes           | Required   | `command`
| `run_pre_commit`                 | No            | \-         |
| `sass`                           | Yes           | Required   | `pathspec`
| `update_readme`                  | Yes           | Optional   | `readme`

#### Details
##### **build**
Method to "poetry" build a package distribution, ie. `poetry build`.

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: build
      confirm: false
      echo_stdout: true
      allow_error: true  # We don't care if no files are clean or if dirs don't exist.
```

This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line.

##### **clean**
Method to delete build artifacts, ie. `rm -rf build \*.egg-info`.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: clean
      confirm: false
      allow_error: true
```

This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line (confirm: false is set on the step).

##### **git_add**
Method to perform a `git add <pathspec>` operation.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: git_add
      arguments:
        pathspec: "app/version.py"
    - method: ...
      ...
```

###### Arguments
- `pathspec` Optional path specification of dir(s) and/or file(s) to stage. Default if not specified is `.`.

##### **git_commit**
Method to perform a `git commit <pathspec>` operation.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: git_commit
      arguments:
        pathspec: "app/version.py" # Optional
        message: "My commit"       # Optional
    - method: ...
      ...
```
###### Arguments
* `pathspec` Optional path specification of dir(s) and/or file(s) to commit. Default if not specified is `.`.
* `message` Optional commit message. Default if not specified is today's date (in format: ~yyyymmddThhmm~).

##### **git_commitversionfiles**
Specialised method (really a customised version of `git_commit`) to git stage and git commit two files relevant to the build process: `pyproject.toml` and `README.(org|md)`.

Specifically, other methods will update these files for version management and this method is provided to get them into git on behalf of a release. Alternately, you can use the more general `git_commit` method, specifying these two files to be added.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...

    - method: git_commit_version_files

    - method: ...
      ...
```

This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line.

##### **git_createrelease**
Method to create a git **release** using the appropriate version string (from `pyproject.toml`).
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...

    - method: git_create_release

    - method: ...
      ...
```
This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line.

##### **git_createtag**
Method to create a local git **tag** using the appropriate version string (from `pyproject.toml`).
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...

    - method: git_create_tag

    - method: ...
      ...
```
This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line.

##### **git_pushtogithub**
Method command to perform a `git push --follow-tags`.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...

    - method: git_push_to_github

    - method: ...
      ...
```
This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line.

##### **pandoc_convertorgtomarkdown**
Specialised method to convert an emacs .org file to an markdown (.md) file using pandoc; specifically:

```shell
pandoc -f org -t markdown --wrap none --output <path_md> <path_org>
```

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: git_add
      arguments:
        pathspec: "app/version.py"
    - method: ...
      ...
```
###### Arguments
* `path_md` Required, path specification input markdown file, e.g. `./docs/my_doc.md`.
* `path_org` Required, path specification resulting .org file to be created, e.g. `./docs/my_doc.org`.

##### **poetry_bumpversion**
Specialised method to "bump" the version of a project/package using Poetry's version command. Takes one of three pre-defined version levels to bump and updates `pyproject.toml` with the new version value.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...

    - method: poetry_bump_version
      arguments:
        poetry_version: patch   # Could also be minor or major.

    - method: ...
      ...
```
###### Arguments
* `poetry_version` Required, the default level of version "bump" to perform. Must be one of 'patch', 'minor', 'major', 'prepatch', 'preminor', 'premajor', 'prerelease' (see [Poetry version command](https://python-poetry.org/docs/cli/#version) for more information).

##### **poetry_lockcheck**
Method to perform a poetry lock "check" to verify that `poetry.lock` is consistent with `pyproject.toml`. If it isn't, will update/refresh `poetry.lock` (after confirmation).
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: poetry_lock_check
```
This command takes **no** arguments but **will** ask for confirmation before running `poetry lock` unless `--no-confirm` is set on the command-line.

##### **publish_topypi**
Method to publish your package to PyPI.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: publish_to_pypi
```
This command takes **no** arguments but **will** ask for confirmation unless `--no-confirm` is set on the command-line as it will update the current `poetry.lock` file.

##### **run_command**
General method to run essentially any local command for it's respective side-effects. 

For example, in one of my projects, I don't use the version number in `pyproject.toml` but instead in an `app/version.py` that is updated from a small script (using the date & respective branch of the last git commit performed).

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: ...
      ...

    - method: run_command
      allow_error: false
      arguments:
        command: "./app/cli/update_settings.py"
```
This command **will** ask for confirmation unless `--no-confirm` is set on the command-line.

###### Arguments
* `command` Required, a string containing the full shell command to execute.

##### **run_precommit**
Method to run the `pre-commit` tool (if you use it).
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: run_pre_commit
      allow_error: false
```
This command takes no argument and **will** ask for confirmation unless `--no-confirm` is set on the command-line.

##### **sass**
Method to run a `sass` command to convert scss to css.
``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: sass
      arguments:
        pathspec: "./app/static/css/sass/mystyles.scss ./app/static/css/mystyles.css"
    - method: ...
      ...
```
###### Arguments
* `pathspec` Required path specification of dir(s) and/or file(s) to run.

##### **update_readme**
Specialised method to move "Unreleased" items into a dedicated release section of a README file.

- README file can be in either [Org](https://orgmode.org/) or Markdown format, ie. `README.md` or `README.org`.
- We assume `README.org/md` is in the same directory as your `pyproject.toml` and `manage.yaml`. This is almost always the root directory of your project.

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: update_readme
      arguments:
        readme: ./docs/README.txt
```

``` yaml
build_my_package:
  description: Build my distribution package.
  steps:
    - method: update_readme     # Will look for either README.org or README.md!
```
This command **will** ask for confirmation unless `--no-confirm` is set on the command-line.

###### Arguments
* `readme` Optional, a string that represents a full path to your respective README.\* file. If not specified, we search for `./README.org` and `./README.md` in the same directory as your `pyproject.toml`.

### README Files
One of the core time-saving's feature of release automation is the stage change of outstanding items addressed in a release to a "completed" state. Since we're not assuming the use of any particular ticket tracking environment, we allow for change management tracking within a README file. Specifically:

* Tracking of closed (but not released) items in an "Unreleased" section of a README.
* Tracking of previous releases and their associated change items by date and release version.

The workflow I use is the following:

* I keep track of all items outstanding using a GTD approach, keeping this list either within a README file or another dedicated environment (usually a .ORG file).
* During development, as GTD items are addressed and committed (also tested, ruff'ed, etc..), I move their entries to the *Unreleased* section of the README file.
* Through a master "release" recipe (or set of recipes), I include the `update_readme` recipe that relabels the *Unreleased* items to the specific release version with today's date (note: doing a `poetry_bump_version` before `update_readme` is important as otherwise, an old version identifier will be used!).

README files are usually one of two formats, .org or .md. In either case, we assume that *Unreleased* appears on a line by itself (irrespective of it's header depth).

#### ORG (.org) Format

A README in org format might be:

``` org
* My Project
* Stuff...
* More Stuff...
* Releases
** Unreleased
   - FIX: Made the gizmo fit into the whatchamacallit.
   - ADD: Capability to make time go backwards (required confirmation beforehand)
   - CHG: Command-line argument ~--make-me~ is now ~--confirm~.
** v1.5.10 - 2023-05-15
   - FIX: blah blah..
   ....
```

The `update_readme` recipt will use the `Unreleased` tag line and allow subsequent entries to "create" a new release (using the current version number in `pyproject.toml` and today's date), transforming the file to look like the following:

``` org
* My Project
* Stuff...
* More Stuff...
* Releases
** Unreleased
** v1.5.11 - 2023-07-12
   - FIX: Made the gizmo fit into the whatchamacallit.
   - ADD: Capability to make time go backwards (requires confirmation beforehand)
   - CHG: Command-line argument ~--make-me~ is now ~--confirm~.
   ....
** v1.5.10 - 2023-05-15
   - FIX: blah blah..
   ....
```

#### Markdown (.md) Format
Similarly, a README in Markdown format might look like the following (note that the Unreleased line is at a different header level than the org-format example above!):

``` markdown
# My Project

## Stuff
    ...

## Releases

### Unreleased
    - FIX: Made the gizmo fit into the whatchamacallit.
    - ADD: Capability to make time go backwards (requires confirmation beforehand)
    - CHG: Command-line argument ~--make-me~ is now ~--confirm~.

### v1.5.10 - 2023-05-15
    - FIX: blah blah..
    ....
```

We use the `Unreleased` tag line and "create" a new release (using the current version number in `pyproject.toml` and today's date), transforming the file to look like the following:

``` markdown
# My Project

## Stuff
   ...

## Releases

### Unreleased

### v1.5.11 - 2023-07-12
    - FIX: Made the gizmo fit into the whatchamacallit.
    - ADD: Capability to make time go backwards (required confirmation beforehand)
    - CHG: Command-line argument ~--make-me~ is now ~--confirm~.

### v1.5.10 - 2023-05-15
    - FIX: blah blah..
    ....
```

## Development

If you want to help develop this, here's what might this might entail:

- Confirm python version availability, I'm developing on 3.11+ for now (and use [pyenv](https://github.com/pyenv/pyenv) to manage all my versions).

- Setup a .venv using your virtual-env manager of choice (I use `python -m venv .venv`).

- Clone the repo.

- `poetry install` to install requisite dependencies into your venv.

- Set `.envrc` to point top-level directory (i.e. README and pyproject.toml), I use the wonderful [direnv](https://direnv.net/) package to take of this housekeeping. Here's what my
`.envrc` contains, it not only sets the `PYTHON_PATH` appropriately but also takes care of automatically point me to my virtual env:

``` bash
export PYTHONPATH=`pwd`
export VIRTUAL_ENV=$PYTHONPATH/.venv
PATH_add "$VIRTUAL_ENV/bin"
```

- At this point, you should be able to run: `python manage check` against the default `manage.yaml` in the root folder (yes, I do eat my own dog-food ;-).

## Project GTD
### Add a --dry-run or --live option?
- Along with support for a [tool.manager.options] in pyproject.toml where the default action would be either "live" or "dry-run" and the command-line option would be the override to whatever's set there.

- Dry-run would actually list the command to be executed.

### Could the contents of manage.yaml actually BE in pyproject.toml? [tool.manager.configuration]
Or at least, be available there and it not, look to a standalone manage.yaml file as a backup?
### Maybe make print also take a target to print (instead of always printing the whole enchilada?)
### Arghhh : Print is broken? (at least in optimus-ludos):

``` shell
% manage print
Traceback (most recent call last):
  File "/Users/peter/Repository/10-19 Development/10 Development/10.01 optimus_ludos/.venv/bin/manage", line 10, in <module>
    sys.exit(main())
             ^^^^^^
  File "/Users/peter/Repository/10-19 Development/10 Development/10.01 optimus_ludos/.venv/lib/python3.11/site-packages/manage/cli.py", line 182, in main
    dispatch(configuration, recipes)
  File "/Users/peter/Repository/10-19 Development/10 Development/10.01 optimus_ludos/.venv/lib/python3.11/site-packages/manage/dispatch.py", line 16, in dispatch
    return _print(configuration, recipes, None)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/peter/Repository/10-19 Development/10 Development/10.01 optimus_ludos/.venv/lib/python3.11/site-packages/manage/methods/_print.py", line 9, in main
    if step.verbose:
       ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'verbose'
```
### When/if we ever release, add support for user/project specific method to be added
### Add back ability to take and reflect command-line options obo method arguments.
For example, `poetry_version` for `update_readme`. Make use of method's "arguments" meta-data now available.

Another example is from raindrop-io-py where we'd like to make the patch, minor, major version bump a single step (right now, we need a unique step for each one :-()
### Create a `sample` recipe to create an example `manage.yaml` in the current project directory.
Thist be essentially a copy of `manage/examples/manage.yaml` to `$HOME_DIR` (while checking to not overwrite any existing file)
### Is it worth refactoring methods to use a common-base class?

Mighnificantly reduce duplicate code associated with confirmation and return statuses?

### Handle steps to support Sphinx documentation management:

- Pursion from pyproject.toml and push to docs/source/conf.py (if it exists)
- (d think we need anything else as pushing to gh will automatically trigger a new RTD build)

### Can we refactor and dynamically create the `GITHUB_PROJECT_RELEASE_HISTORY` URL?

We khe package name (from pyproject.toml) - 90% confidence We know the user name (from another env variable) - 100% confidence We can somewhat surely assume the default branch? - 50% confidence.

### Replace requests and vcrpy with [Gracy](https://github.com/guilatrova/gracy)?
### Status of ONGOING test development:

  | Status   | Module
  | -------- | ----------------------------------
  | 0%       | `build`
  | 100%     | `clean`
  | 100%     | `git_add`
  | 100%     | `git_commit`
  | 0%       | `git_create_release`
  | 0%       | `git_create_tag`
  | 0%       | `git_push_to_github`
  | 100%     | `pandoc_convert_org_to_markdown`
  | 0%       | `poetry_bump_version`
  | 0%       | `poetry_lock_check`
  | 0%       | `publish_to_pypi`
  | 0%       | `run_command`
  | 0%       | `run_pre_commit`
  | 0%       | `sass`
  | 100%     | `update_readme`
  | -------- | ----------------------------------

## Release History
### Unreleased
### v0.1.11 - 2023-09-06

- FIXED: Address vulnerability of gitpython (CVE-2023-40590).

### v0.1.10 - 2023-08-17

- FIXED: Address removal of e-Tugra root certificate from certifi library (CVE-2023-37920).

### v0.1.9 - 2023-07-20

- FIXED: Add missing "main" dependency on `gitpython` (was coming implicitly from pytest-git but we need it for releases explicitly).

### v0.1.8 - 2023-07-19

- CHANGED: Removed argument "pathspec" from `git_commit`, all staged items are now committed (only argument is optional commit message).
- INTERNAL: Add more consistency obo use of `verbose` and `confirm` options.
- INTERNAL: Added tests for `git_add` and `git_commit` methods.

### v0.1.7 - 2023-07-18

- CHANGED: Removed method `poetry-lock-refresh`. The underlying command `poetry lock --no-update` will be done automatically (net of confirmation) as part of the `poetry-lock-check` method.
- CHANGED: Moved up to python 3.11 (specifically 3.11.3) to take advantage of built-in TOML support. Contact me if you think it's important to you that I support backwards compatibility with older python versions (that don't have tomllib built-in).
- CHANGED: Pulled (limited) support for method-specific command-line argument setting until we deal with method meta-data better (was only used for 1 argument: `poetry_version` to bump).
- INTERNAL: Incorporate use of [pytest-git](https://pypi.org/project/pytest-git/) to begin structured testing of git methods.

### v0.1.6 - 2023-07-15

- ADD: `sass` method to pre-process SCSS to CSS files.
- ADD: General `git_add` method to stage file(s) to local repository.
- FIX: Bug in identification of optionally-typed arguments (albeit not clear if used anywhere).

### v0.1.5 - 2023-07-12

- CHANGED: For method `update_readme`, we relaxed the requirement on finding README files. Specifically, by default, we search for either README.org or README.md and use the first one found. You can also specify a path to a README file directly with a `readme` argument to the method (ie, instead of `readme_format`).
- CHANGED: We resolved difference between the built-in targets "show" and "print". It's not "print" consistently (no more "show" option).

### v0.1.4 - 2023-07-10

- ADDED: "print" as a new built-in target (essentially just validates and prints the relevant manage.yaml command file to your terminal).
- ADDED: A simple "`git_add`" method that simply does a `git add {pathspec}` (or 'git add .' if pathspec is not provided).
- ADDED: A "`run_command`" method to run an arbitrary local command.
- CHANGED: Missing either \[tool.poetry\].version or \[tool.poetry\].package is now allowed (for those projects that don't need formal package release/build management).

### v0.1.3 - 2023-07-09

- ADDED: Two commands on behalf of poetry lock file management: `poetry_lock_check` and `poetry_lock_refresh` (meant to be used in that order) for good security practice.

### v0.1.2 - 2023-02-18

- ADDED: Command-line argument to display package' version and quit.

### v0.1.1 - 2023-02-16

### v0.1.0 - 2023-02-16

- ADDED: Support for step-specific command-line overrides. For example, when "bumping" the version number of a package, while the recipe's step may default to **patch**, we can now specify **minor** (or any of the Poetry version labels) on the command-line instead, e.g. `--poetry-version`.
- ADDED: Ability to override "confirm" recipe step attribute with command-line flag: `--no-confirm` or `--confirm`.

### v0.0.14 - 2023-02-06

- ADDED: Ability for `update_readme` to take an argument specifying what format the project's README file is in, ie. 'md' for markdown (default) or 'org'. Optional argument is `readme_format`.

### v0.0.13 - 2023-02-02

- ADDED: Ability to pass general "arguments" into steps that might require `manage.yaml` time configuration. Example is a step to convert from org to markdown, arguments are used to pass the specific input & output paths.
- CHANGED: Added ability for built-in "show" target to render nested recipes.

### v0.0.12 - 2023-02-02

- ADDED: A step method that uses pandoc converter, for example to go from README.org to README.md.
- ADDED: The first draft of a better "show" target to document the current `manage.yaml` file.
- CHANGED Corrected data model: instead of `method` or `step` for a recipe, it's now `method` or *recipe*.
- CHANGED: Moved back to dynamically importing available step methods from manage.steps module.

### v0.0.11 - 2023-01-29

- ADDED: A 'quiet-mode' step configuration option to remove all extraneous non-failure associated terminal output.
- ADDED: A command-line parameter to point to a specific manage recipe file (instead of default manage.toml)
- CHANGED: Back to YAML instead of TOML for recipe files (TOML nice for serialisation but too verbose for our use case).
- CHANGED: Default value for 'confirm' step option to True (as most of my steps are using True).
- CHANGED: To pydantic for stronger typing of Recipes and their associated steps.
- CHANGED: Sample recipe toml files to match pydantic-based data models (in particular, recipes are a dict!).

### v0.0.10 - 2023-01-26

- ADDED: A "check" recipe/option to simply run the setup & validation steps only.
- ADDED: A validation that the version in `pyproject.toml` is consistent with the last release in the Release History of `README.org`.
- CHANGED: Terminology from `target` to `recipe` and manage.toml to consisting of *recipes*.
- CHANGED: Steps to make them more "granular" and loaded from `steps` module.
- CHANGED: Over to TOML (tomli) instead of YAML for recipe files.

### v0.0.9 - 2023-01-25

- CHANGED: To catch exception when manage.yaml can't be opened.

### v0.0.8 - 2023-01-25

- ADDED: Missing /bin/manage script for execution after pip/poetry install.

### v0.0.7 - 2023-01-25

- ADDED: Assumptions and example configurations to README.org.

### v0.0.2 - 2023-01-25

- Initial packaging.
