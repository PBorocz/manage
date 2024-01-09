# Manage
## Introduction

In learning how to perform releases to PyPI, I became somewhat "disenchanted" by all the various manual steps and required.

In the spirit of GTD, a Makefile (or personal favorite [Justfile](https://github.com/casey/just)) was a good starting point.

However, even these left something to be desired which led me to [Thomas Feldman\'s manage.py](https://github.com/tfeldmann/organize/blob/main/manage.py) environment. I wanted to combine the best of Justfile's and Thomas' environment through a stand-alone package that I could easily apply to my myriad python projects (irrespective of whether they're released as formal packages).

Thus, this package automates all the common operations for [Poetry](https://python-poetry.org/) & README-based project/package management that I perform on a day-to-day basis. In particular, those that I don't perform regularly and/or require multiple steps to perform (and thus, tend to forget how to do!)

Here's an example of building and releasing a python package:

![Sample Session](Screenshot.png)

## Design

- Every granular command that might need to be performed on behalf of project/package management is packaged as a `method` (e.g. poetry build, git commit, sass etc.)

- These granular methods are combined into `recipes` to perform a particular task (e.g. build my project, update my release notes etc.)

- Recipes can be _nested_ (analogous to cooking recipes where one recipe may refer to another for a component).

- Recipes are stored in your project's `pyproject.toml` file following the `tool` section format used by other python tools. In this case, `[tool.manage]`.

- The `[tool.manage.recipes]` section contains:

    - A set of *targets* aka recipes (terminology synonymous with Makefile/Justfile targets).

    - Each target consists of a set of steps, each of which is shorthand description of what needs to be accomplished.

    - Each step can refer either to a built-in **method** (e.g. `clean`) or to the name of another *recipe*.

- Each step in a target is also configured by the following parameters:

    - Steps that have a side-effect (ie. those that can *change* something) can have a user-confirmation before executing, e.g. "Are you sure? (`confirm`).

    - Each step can be configured control whether errors encountered are fatal or not (`allow_error`).

- For each command within the step, the contents of either `stdout` or `stderr`  man displayed based on the return code of the command's execution. Specifically, on a non-zero return status, `stderr` will always be displayed. For a return code of zero, `stdout` will be displayed if `verbose` mode is active for the respective step.

- Other command-line defaults that can be set in this section are: `confirm` and `dry-run`.

### Example

An example `[tool.manage]` section that defines three targets (bump a version number, clean our build environment and build our package (after cleaning) might look like this:

``` toml
################################################################################
[tool.manage]
verbose = true  # Remember that in TOML, it's lowercase true/false!
confirm = true
dry_run = true

#-------------------------------------------------------------------------------
[[tool.manage.recipes.bump]]
description = "Bump the version number to the next /patch/ level and commit locally"

[[tool.manage.recipes.bump.steps]]
method = "poetry_version"

[[tool.manage.recipes.bump.steps]]
method = "update_readme"

[[tool.manage.recipes.bump.steps]]
method = "git_commit_version_files"

#-------------------------------------------------------------------------------
[[tool.manage.recipes.clean]]
description = "Clean out our temp files and ALL previous builds."

[[tool.manage.recipes.clean.steps]]
method = "clean"
confirm = false
allow_error = true

#-------------------------------------------------------------------------------
[[tool.manage.recipes.build]]
description = "Build our distribution(s)."

[[tool.manage.recipes.build.steps]]
recipe = "clean"

[[tool.manage.recipes.build.steps]]
method = "build"
confirm = false
allow_error = false
```

Note: If you want "non-standard" recipe names (for instance, in some projects, I like to name my recipes by the rough order of execution: 1\_bump, 2\_build, 3\_release), you can do that by quoting the respective string:


``` toml
#-------------------------------------------------------------------------------
[[tool.manage.recipes."1_bump"]]
description = "Bump the version number to the next /patch/ level and commit locally"

[[tool.manage.recipes."1_bump".steps]]
method = "poetry_version"

[[tool.manage.recipes."1_bump".steps]]
method = "poetry_version_sync"

[[tool.manage.recipes."1_bump".steps]]
method = "update_readme"

[[tool.manage.recipes."1_bump".steps]]
method = "git_commit_version_files"
```

## Assumptions

This tool is based on _my_ common python project standards, allowing for the ability of this tool to work seamlessly for _me_. To the degree that your development/project/release environment strays from mine, the tool might become less relevant.

### Tools

- We assume [Git/Github](https://github.com) are used for code version management.
- We assume [poetry](https://python-poetry.org) is used to manage package dependencies **and** build environment.
- We assume that execution of this script is from the TOP level of a project, i.e. at the same level as pyproject.toml.
- We assume that **version string** in `pyproject.toml` is the **_SINGLE_** and **_CANONICAL_** version string in our project/package.

Specifically, there are no `/module/__version__.py`\'s or versions embedded in `__init__.py~` files (Should you want/need to have these, it\'s certainly possible to automate the creation of them based on the version from `pyproject.toml`!).

### Versioning

We assume the use of semantic versioning with `poetry version` to update/manage our version number. Specifically, this allows us to use `poetry version` command\'s bump rules for version updates, ie. patch, minor, major etc.

### CHANGELOG/Release History Management

We do **not** use a stand-alone `CHANGELOG` file, instead we use a specific section in `README.org/md`. We assume that list of completed but unreleased items exist under an "**Unreleased**" header. This format provides reasonably clean automation of version/release management within the README file.

## Installation

While this isn't packaged for PyPI release, build/distribution files (ie. wheel and tgz) are released to github.

### Global (recommended)

To install on a "global" basis, ie. as a common-tool across multiple projects, I heartily recommend the use of [pipX](https://pipx.pypa.io/stable/). For example:

``` shell
% pipx install git+https://github.com/PBorocz/manage
```

This will create a standalone virtual environment (usually `~/.local/pipx/venvs`) dedicated to `manage` *and* put `manage` on your path (usually in `~/.local/bin`)

### Local

If you want to keep the installation local to your respective project, you can install `manage` from git into your local project environment just like any other package:

``` shell
% poetry add git+https://github.com/PBorocz/manage --group dev
```
 
This will create a `manage` command into your virtual environment's /bin environment (your project *IS* running in a virtual environment...right? ;-).

## Confirmation

Since the basis of `manage` is the availability of a `pyproject.toml` file, you need to run `manage` from any directory that has a `pyproject.toml` in it (ie. usually your project root directory).

At this point, you should be able to run: `% manage --validate` and your environment will be checked.

Since you probably don't *have* anything specific to `manage` yet, append the following snippet to your `pyproject.toml`:

``` toml
# ----------------------------------------------------------------------------------
# To build, we first clean out previous builds and then ask Poetry to do it's stuff.
# ----------------------------------------------------------------------------------
[tool.manage.recipes.build]
description = "Build our distribution(s)."

[[tool.manage.recipes.build.steps]]
recipe = "clean"

[[tool.manage.recipes.build.steps]]
method = "poetry_build"
confirm = false
allow_error = false

# ---------------------------------------------------
# Clean as a separate (albeit trivially easy) recipe.
# ---------------------------------------------------
[tool.manage.recipes.clean]
description = "Clean out our temp files and ALL previous builds."

[[tool.manage.recipes.clean.steps]]
method = "clean"
allow_error = true

```

After which `manage --print` should print it's respective contents:

``` shell
% manage --print build

build ≫ Build our distribution(s).
[
    {
        'recipe': 'clean',
        'confirm': False,
        'verbose': False,
        'debug': False,
        'allow_error': None,
        'arguments': {}
    },
    {
        'method': 'poetry_build',
        'confirm': False,
        'verbose': False,
        'debug': False,
        'allow_error': False,
        'arguments': {}
    }
]

clean ≫ Clean out our temp files and ALL previous builds.
[
    {
        'method': 'clean',
        'confirm': False,
        'verbose': False,
        'debug': False,
        'allow_error': True,
        'arguments': {}
    }
]

%
```

## Environment Requirements

Several of the built-in methods make assumptions about your configuration, either specific environment variables necessary or specific executable(s) on your path. Several of these are rather fundamental to the operation of the system, e.g. `git` (on behalf of `git_add`, `git_commit` etc.), `poetry` (on behalf of `poetry_build`, `poetry_version` etc.). However, there are a few specialty commands that your environment will need to support if you want to use them. Here's the list of all external executables that may need to be on your path:

| Executable   | Method(s)                             |
|--------------|---------------------------------------|
| `git`        | All methods that start with `git_`    |
| `poetry`     | All methods that start with `poetry_` |
| `pandoc`     | `pandoc_convert_org_to_markdown`      |
| `pre-commit` | `pre_commit`                          |
| `sass`       | `sass`                                |

The `git_create_release` method uses the `requests` package to access the `github` API to create a git release. Thus, for this method, we require the following entries are available in our environment (either set in your respective shell or through .env):

| Environment Variable               | Explanation            | Example
| ---------------------------------- | ---------------------- | --------------------------------------------------------------------------------
| `GITHUB_USER`                      | User id                | `John-Jacob_JingleheimerSchmidt`
| `GITHUB_API_TOKEN`                 | Personal API token     | `ghp_1234567890ABCDEFG1234567890`
| `GITHUB_API_RELEASES`              | URL to release API     | `https://api.github.com/repos/><user>/<project>/releases`
| `GITHUB_PROJECT_RELEASE_HISTORY`   | URL to release history | `https://github.com/<user>/<project>/blob/<mainline_branch>/README.org#release-history`

## Command-Line Arguments
### --confirm

Require a priori confirmation for all methods that may make state changes. Default is False.

### --verbose/-v

Displays an extra-level of output regarding method execution (for example, including a method command's stdout stream if available). Default is False.

### --debug

Displays internal debugging information (not high-volume). Default is False

### --dry_run/--live

Run all steps in either `dry_run` or `live` mode, overriding any settings within recipe step definitions. Default is `dry_run` of True.

### --print

Does a "pretty-print" of your recipe configuration either for either recipes or just the specific target if provided and exits. For example:
	
``` shell
% manage --print build

build ≫ Build our distribution(s)
[
    {
        'method': 'poetry_lock_check',
        'confirm': False,
        'verbose': False,
        'allow_error': False,
        'arguments': {}
    },
    {
        'recipe': 'clean',
        'confirm': False,
        'verbose': False,
        'allow_error': False,
        'arguments': {}
    },
    {
        'method': 'poetry_build',
        'confirm': False,
        'verbose': False,
        'allow_error': False,
        'arguments': {}
    }
]

%
```

### --<method\>:<argument\>

Provide a method a specific argument value. For example, the `git_commit` method supports an optional git commit message. This can be either be supplied on a standardized basis in your `pyproject.toml` file like this:
	
``` toml
[[tool.manage.recipes.<aRecipeName>.steps]]
	method = "git_commit"
	confirm = true
	arguments: {message = "Auto Commit"}
```	

or overridden from the command-line:

``` shell
% manage 1_bump --git_commit:message "Build of $(date +'%Y-%m-%d')" --poetry_version:bump_level minor
```

I commonly use the `poetry_version:bump_level` argument for flexibility in changing the semantic version/level of a release without needing to define multiple recipes (ie. release a `patch`, another for `minor` etc.).

## Methods Available

A detailed list of all the built-in methods available for your recipes can be found [here](docs/method_details.md).

## Release History
### Unreleased

- INTERNAL: Upgraded to pydantic 2.5.3 from 1.* version (well worth it!)

### v0.3.4 - 2024-01-07

- FIX: Bug in methods that use the "current" version of the project (eg. git\_create\_release). Now, we re-read the `pyproject.toml` file in case a previous step within the same execution might have updated the version (specifically, the `poetry_version` method). 

- FIX: Bug in `sass` method that didn't support multiple paths on the method's pathspec argument. 
 
### v0.3.3 - 2024-01-04

- ADD: New command-line argument `--validate` to validate steps _all_ recipes defined (and exit).

### v0.3.2 - 2024-01-03

- ADD: New command-line argument `--version` to display current package version (and exit).

- ADD: New method `poetry_version_sync` to keep `__version__` attribute of a python file (usually `<module>/__init__.py`) up to date with the version in `pyproject.toml` (without have to resort to `importlib.metadata` approach).

### v0.3.1 - 2023-12-31

- Miscellaneous updates to diagnostics and added method specific validation.

### v0.3.0 - 2023-12-30

- **BREAKING** CHANGE: Changed the name of the `pre-commit` method to `pre_commit` (previously was `run_pre_commit`).

- **BREAKING** CHANGE: Changed the name of the command to publish a package to PyPI to `poetry_publish` (previously was `publish_to_pypi`).

- **BREAKING** CHANGE: Changed the name of the command to run arbitrary script to `command` (previously was `run_command`).

- **BREAKING** CHANGE: Removed the ability to set command-line defaults in the `[tool.manage.defaults]` section of `pyproject.toml`.

- CHANGE: Command-line overrides to method arguments are now _specific_ to the method. For example, if your `pyproject.toml` file contained the default argument to poetry\_version's bump\_level to be _patch_ (as that's your most common release), but you wanted to perform a _major_ release, simply override the bump_level on the command-line:

``` shell
% manage 1_bump ... --poetry_version:bump_level major 
```

- ADD: New command-line flag `--debug` for more detailed/operational debugging output.

### v0.2.1 - 2023-12-26

- FIX: Minor updates to README.md file.

### v0.2.0 - 2023-12-26

- CHANGE: **BREAKING!** -> Move from standalone `manage.yaml` to reading targets & recipes directly into project's respective `pyproject.toml`. Conversion can be as easy as using ChatGPT (or ilk) to convert from yaml to toml and inserting the `tool.manage` prefix.

- CHANGE: **BREAKING!** -> Renamed `poetry_bump_version` method to `poetry_version` to more closely align with Poetry's command structure. Similarly, the method's argument `poetry_version` is now `bump_rule`.

- CHANGE: Added support for command-line options on behalf of methods that require arguments. For instance, the specific `poetry_version` to go "up to" (aka "bump level" in poetry parlance) was an argument setting on the respective step definition in `pyproject.toml` (e.g. patch or minor). While a default value of "patch" is sufficient for most releases, if a "minor" release was required, the `pyproject.toml` argument would need to be manually changed. Now, the following will work:

- CHANGE: The `print` target is now simply a command-line flag, that runs and then exits; for example:

``` shell
# To print all recipes define in pyproject.toml:
% manage --print

# or, to print a specific recipe/target:
% manage --print build
```

- CHANGE: Removed unused `echo-stdout` step attribute (mostly in documentation), wasn't actually implemented as we use `verbose` instead.

- CHANGE: Removed unused `no-confirm` documentation (wasn't actually implemented either).

``` shell
% manage build --bump_rule minor
```

Note that there are several arguments that are COMMON across methods (e.g. pathspec on behalf of `git-add`, `git-commit` and `sass`). Setting a `pathspec` value on the command-line will apply to *all* the steps run in the respective target. Let me know if this is a significant issue and I'll move to a "step-specific" approach.

- INTERNAL: Added support for pre-commit trigger and implementation of ruff (lint and format) and unimport.

- INTERNAL: Refactored ALL method implementations to class-based (didn't save as much code as expected but seems a bit cleaner).


### v0.1.11 - 2023-09-06

- FIX: Address vulnerability of gitpython (CVE-2023-40590).

### v0.1.10 - 2023-08-17

- FIX: Address removal of e-Tugra root certificate from certifi library (CVE-2023-37920).

### v0.1.9 - 2023-07-20

- FIX: Add missing "main" dependency on `gitpython` (was coming implicitly from pytest-git but we need it for releases explicitly).

### v0.1.8 - 2023-07-19

- CHANGE: Removed argument "pathspec" from `git_commit`, all staged items are now committed (only argument is optional commit message).
- INTERNAL: Add more consistency obo use of `verbose` and `confirm` options.
- INTERNAL: Added tests for `git_add` and `git_commit` methods.

### v0.1.7 - 2023-07-18

- CHANGE: Removed method `poetry-lock-refresh`. The underlying command `poetry lock --no-update` will be done automatically (net of confirmation) as part of the `poetry-lock-check` method.
- CHANGE: Moved up to python 3.11 (specifically 3.11.3) to take advantage of built-in TOML support. Contact me if you think it's important to you that I support backwards compatibility with older python versions (that don't have tomllib built-in).
- CHANGE: Pulled (limited) support for method-specific command-line argument setting until we deal with method meta-data better (was only used for 1 argument: `poetry_version` to bump).
- INTERNAL: Incorporate use of [pytest-git](https://pypi.org/project/pytest-git/) to begin structured testing of git methods.

### v0.1.6 - 2023-07-15

- ADD: `sass` method to pre-process SCSS to CSS files.
- ADD: General `git_add` method to stage file(s) to local repository.
- FIX: Bug in identification of optionally-typed arguments (albeit not clear if used anywhere).

### v0.1.5 - 2023-07-12

- CHANGE: For method `update_readme`, we relaxed the requirement on finding README files. Specifically, by default, we search for either README.org or README.md and use the first one found. You can also specify a path to a README file directly with a `readme` argument to the method (ie, instead of `readme_format`).
- CHANGE: We resolved difference between the built-in targets "show" and "print". It's not "print" consistently (no more "show" option).

### v0.1.4 - 2023-07-10

- ADD: "print" as a new built-in target (essentially just validates and prints the relevant manage.yaml command file to your terminal).
- ADD: A simple "`git_add`" method that simply does a `git add {pathspec}` (or 'git add .' if pathspec is not provided).
- ADD: A "`run_command`" method to run an arbitrary local command.
- CHANGE: Missing either \[tool.poetry\].version or \[tool.poetry\].package is now allowed (for those projects that don't need formal package release/build management).

### v0.1.3 - 2023-07-09

- ADD: Two commands on behalf of poetry lock file management: `poetry_lock_check` and `poetry_lock_refresh` (meant to be used in that order) for good security practice.

### v0.1.2 - 2023-02-18

- ADD: Command-line argument to display package' version and quit.

### v0.1.1 - 2023-02-16

### v0.1.0 - 2023-02-16

- ADD: Support for step-specific command-line overrides. For example, when "bumping" the version number of a package, while the recipe's step may default to **patch**, we can now specify **minor** (or any of the Poetry version labels) on the command-line instead, e.g. `--poetry-version`.
- ADD: Ability to override "confirm" recipe step attribute with command-line flag: `--no-confirm` or `--confirm`.

### v0.0.14 - 2023-02-06

- ADD: Ability for `update_readme` to take an argument specifying what format the project's README file is in, ie. 'md' for markdown (default) or 'org'. Optional argument is `readme_format`.

### v0.0.13 - 2023-02-02

- ADD: Ability to pass general "arguments" into steps that might require `manage.yaml` time configuration. Example is a step to convert from org to markdown, arguments are used to pass the specific input & output paths.
- CHANGE: Added ability for built-in "show" target to render nested recipes.

### v0.0.12 - 2023-02-02

- ADD: A step method that uses pandoc converter, for example to go from README.org to README.md.
- ADD: The first draft of a better "show" target to document the current `manage.yaml` file.
- CHANGED Corrected data model: instead of `method` or `step` for a recipe, it's now `method` or *recipe*.
- CHANGE: Moved back to dynamically importing available step methods from manage.steps module.

### v0.0.11 - 2023-01-29

- ADD: A 'quiet-mode' step configuration option to remove all extraneous non-failure associated terminal output.
- ADD: A command-line parameter to point to a specific manage recipe file (instead of default manage.toml)
- CHANGE: Back to YAML instead of TOML for recipe files (TOML nice for serialisation but too verbose for our use case).
- CHANGE: Default value for 'confirm' step option to True (as most of my steps are using True).
- CHANGE: To pydantic for stronger typing of Recipes and their associated steps.
- CHANGE: Sample recipe toml files to match pydantic-based data models (in particular, recipes are a dict!).

### v0.0.10 - 2023-01-26

- ADD: A "check" recipe/option to simply run the setup & validation steps only.
- ADD: A validation that the version in `pyproject.toml` is consistent with the last release in the Release History of `README.org`.
- CHANGE: Terminology from `target` to `recipe` and manage.toml to consisting of *recipes*.
- CHANGE: Steps to make them more "granular" and loaded from `steps` module.
- CHANGE: Over to TOML (tomli) instead of YAML for recipe files.

### v0.0.9 - 2023-01-25

- CHANGE: To catch exception when manage.yaml can't be opened.

### v0.0.8 - 2023-01-25

- ADD: Missing /bin/manage script for execution after pip/poetry install.

### v0.0.7 - 2023-01-25

- ADD: Assumptions and example configurations to README.org.

### v0.0.2 - 2023-01-25

- Initial packaging.

## APPENDIX: Development

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

## APPENDIX: README Files & Formats
One of the core time-saving's feature of release automation is the stage change of outstanding items addressed in a release to a "completed" state. Since we're not assuming the use of any particular ticket tracking environment, we allow for change management tracking within a README file. Specifically:

* Tracking of closed (but not released) items in an "Unreleased" section of a README.
* Tracking of previous releases and their associated change items by date and release version.

The workflow I use is the following:

* I keep track of all items outstanding using a GTD approach, keeping this list either within a README file or another dedicated environment (usually a .ORG file).

* During development, as GTD items are addressed and committed (also tested, ruff'ed, etc..), I move their entries to the *Unreleased* section of the README file.

* Through a master "release" recipe (or set of recipes), I include the `update_readme` recipe that relabels the *Unreleased* items to the specific release version with today's date (note: doing a `poetry_version` before `update_readme` is important as otherwise, an old version identifier will be used!).

README files are usually one of two formats, .org or .md. In either case, we assume that *Unreleased* appears on a line by itself (irrespective of it's header depth).

### ORG (.org) Format

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

### Markdown (.md) Format
Similarly, a README in Markdown format might look like the following (note that the Unreleased line is at a different header level than the org-format example above!):

``` markdown
# My Project

## Stuff
    ...

## Releases

### Unreleased
### v0.3.4 - 2024-01-07
### v0.3.2 - 2024-01-04
### v0.3.2 - 2024-01-04
### v0.3.2 - 2024-01-03
### v0.3.2a0 - 2024-01-03
### v0.3.1 - 2023-12-31
### v1.9.11 - 2023-12-30
### v1.9.11 - 2023-12-30
### v1.9.11 - 2023-12-30
### v0.3.0 - 2023-12-30
### v0.2.1 - 2023-12-26
### v0.2.0 - 2023-12-26
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
### v0.3.4 - 2024-01-07
### v0.3.2 - 2024-01-04
### v0.3.2 - 2024-01-04
### v0.3.2 - 2024-01-03
### v0.3.2a0 - 2024-01-03
### v0.3.1 - 2023-12-31
### v1.9.11 - 2023-12-30
### v1.9.11 - 2023-12-30
### v1.9.11 - 2023-12-30
### v0.3.0 - 2023-12-30
### v0.2.1 - 2023-12-26
### v0.2.0 - 2023-12-26

### v1.5.11 - 2023-07-12
    - FIX: Made the gizmo fit into the whatchamacallit.
    - ADD: Capability to make time go backwards (required confirmation beforehand)
    - CHG: Command-line argument ~--make-me~ is now ~--confirm~.

### v1.5.10 - 2023-05-15
    - FIX: blah blah..
    ....
```

