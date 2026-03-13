# changes-semver

[![build](https://github.com/jbmorley/changes/actions/workflows/build.yaml/badge.svg)](https://github.com/jbmorley/changes/actions/workflows/build.yaml)

Lightweight and (hopefully) unopinionated tool for using [Conventional Commits](https://www.conventionalcommits.org/) and [Semantic Versioning](https://semver.org) with [Git](https://git-scm.com).

## Overview

Many of the Semantic Versioning tools out there force very specific workflows that I found hard to adopt in my own projects. Changes attempts to provide a collection of tools that fit into your own project lifecycle by providing a collection of commands that can be assembled however you need.

Changes differs from many other solutions by using [tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging) to mark commits in your repository as released. This allows releases to be made without modifying the source or making additional commits.

## Installation

Changes is available via [PyPI](https://pypi.org/project/changes-semver/).

Install it using your Python package manager of choice. For example, using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install changes-semver
```

## Usage

Here are a few quick commands you can try to get you started—run these from within a Git repository with commit messages conforming to Conventional Commits:

- Get the current version number:

  ```shell
  changes version --released
  ```
  
- Get the next version number (accounting for changes since the last release tag):

  ```shell
  changes version
  ```

- Get the latest release notes:

  ```shell
  changes notes --released
  ```

- Get the released notes for the next version:

  ```shell
  changes notes
  ```

- List the full history:

  ```shell
  changes notes --all	
  ```

- Make a release:

  ```shell
  changes release
  ```

  (Tags the current sha with the new version if there are unreleased changes).

Find out more details using the `--help` command:

```bash
changes --help
```

Or see the details of specific sub-commands by passing the `--help` flag directly to those commands:

```bash
changes release --help
```

## Development

### Setup

```bash
git clone git@github.com:jbmorley/changes.git
cd changes
pipenv install
```

### Tests

Run tests locally using the `test.sh` script:

```bash
./scripts/test.sh
```

You can run a specific test by specifying the test class on the command line:

```bash
./scripts/test.sh test_cli.CLITestCase.test_version_multiple_changes_yield_single_increment
```
