#!/usr/bin/env python3
#
# Copyright (c) 2021 InSeven Limited
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import collections
import copy
import enum
import logging
import os
import re
import subprocess
import sys
import tempfile

import yaml

import cli


class Type(enum.Enum):
    CI = "ci"
    DOCUMENTATION = "docs"
    FEATURE = "feat"
    FIX = "fix"
    UNKNOWN = "UNKNOWN"


OPERATIONS = {
    Type.CI: None,
    Type.DOCUMENTATION: None,
    Type.FEATURE: lambda commit, version: version.bump_minor(),
    Type.FIX: lambda commit, version: version.bump_patch(),
    Type.UNKNOWN: None,
}


TYPE_TO_SECTION = {
    Type.CI: "Ignore",
    Type.DOCUMENTATION: "Ignore",
    Type.FEATURE: "Changes",
    Type.FIX: "Fixes",
    Type.UNKNOWN: "Ignore",
}


class Chdir(object):

    def __init__(self, path):
        self.path = os.path.abspath(path)

    def __enter__(self):
        self.pwd = os.getcwd()
        os.chdir(self.path)
        return self.path

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.pwd)


class Version(object):

    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.did_update_major = False
        self.did_update_minor = False
        self.did_update_patch = False

    def bump_major(self):
        if self.did_update_major:
            return
        self.major = self.major + 1
        self.minor = 0
        self.patch = 0
        self.did_update_major = True

    def bump_minor(self):
        if self.did_update_minor or self.did_update_major:
            return
        self.minor = self.minor + 1
        self.patch = 0
        self.did_update_minor = True

    def bump_patch(self):
        if self.did_update_patch or self.did_update_minor or self.did_update_major:
            return
        self.patch = self.patch + 1
        self.did_update_patch = True

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other):
        if self.major != other.major:
            return False
        if self.minor != other.minor:
            return False
        if self.patch != other.patch:
            return False
        return True

    def __lt__(self, other):
        if self == other:
            return False
        if self.major > other.major:
            return False
        if self.major < other.major:
            return True
        if self.minor > other.minor:
            return False
        if self.minor < other.minor:
            return True
        if self.patch > other.patch:
            return False
        return True

    def __hash__(self):
        return str(self).__hash__()

    @classmethod
    def from_string(self, string, strip_scope=None):
        return parse_version(string, scope=strip_scope)


class Change(object):

    def __init__(self, message):
        self.message = message

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.message == other.message

    def __str__(self):
        return str(self.message)


class Commit(Change):

    def __init__(self, sha, message, tags, version):
        super().__init__(message)
        self.sha = sha
        self.tags = tags
        self.version = version


class Message(object):

    def __init__(self, type, scope, breaking_change, description):
        self.type = type
        self.scope = scope
        self.breaking_change = breaking_change
        self.description = description

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.type != other.type:
            return False
        if self.scope != other.scope:
            return False
        if self.breaking_change != other.breaking_change:
            return False
        if self.description != other.description:
            return False
        return True

    def __str__(self):
        return self.description


class Release(object):

    def __init__(self, version, changes, is_released=False):
        self.version = version
        self.changes = changes
        self.is_released = is_released

    def set_previous_version(self, previous_version):
        """Recomputes the current version based on the previous version by applying the changes in order."""
        self.version = copy.deepcopy(previous_version)
        for commit in reversed(self.changes):
            if commit.message.type in OPERATIONS and OPERATIONS[commit.message.type] is not None:
                if commit.message.breaking_change:
                    self.version.bump_major()
                else:
                    OPERATIONS[commit.message.type](commit, self.version)
            else:
                logging.warning("Ignoring commit: '%s'", commit.message.description)

    @property
    def is_empty(self):
        for change in self.changes:
            if OPERATIONS[change.message.type] is not None:
                return False
        return True

    def merge(self, release):
        self.changes.extend(release.changes)


class History(object):

    def __init__(self, path, scope=None, history=None, skip_unreleased=False):
        self.path = os.path.abspath(path)
        self.scope = scope
        self.skip_unreleased = skip_unreleased
        self.history = os.path.abspath(history) if history is not None else None
        self._load()

    def _load(self):
        with Chdir(self.path):

            # Get all the changes on the current branch.
            all_changes = get_commits(scope=self.scope)

            # Group the changes by release.
            releases = []
            releases.append(Release(None, []))
            for change in all_changes:
                if change.version is not None:
                    release = Release(change.version, [], is_released=True)
                    releases.append(release)
                releases[-1].changes.append(change)

            # Fix-up the version number for any un-released current release.
            if releases[0].version is None:
                releases[0].set_previous_version(releases[1].version if len(releases) > 1 else Version(0, 0, 0))

            # Remove the empty head release if there's already an active release.
            if len(releases) > 1 and releases[0].is_empty:
                releases.pop(0)

            releases_by_version = {release.version: release for release in releases}

            if self.history is not None:
                for version, release in load_history(path=self.history, scope=self.scope).items():
                    try:
                        releases_by_version[version].merge(release)
                    except KeyError:
                        releases_by_version[version] = release

            releases = list(sorted(releases_by_version.values(),
                                   key=lambda release: release.version, reverse=True))

            if self.skip_unreleased:
                self.releases = [release for release in releases if release.is_released]
            else:
                self.releases = releases

    def format_changes(self):
        return format_releases(self.releases)


def load_history(path, scope=None):
    history = {}
    with open(path) as fh:
        contents = yaml.load(fh, Loader=yaml.SafeLoader)
    # Check the format.
    if not isinstance(contents, dict):
        raise ValueError("Invalid configuration")
    for version_string, changes in contents.items():
        if not isinstance(version_string, str) or not isinstance(changes, list):
            raise ValueError("Invalid configuration")
        messages = [parse_message(change) for change in changes]
        commits = [Change(message=message) for message in messages]
        commits.reverse()
        version = Version.from_string(version_string, scope)
        release = Release(version, commits, is_released=True)
        history[version] = release
    return history


def run(command, dry_run=False):
    if dry_run:
        logging.info(command)
        return []
    result = subprocess.run(command, capture_output=True)
    result.check_returncode()
    lines = result.stdout.decode("utf-8").strip().split("\n")
    return lines


def get_tags(sha):
    try:
        return run(["git", "describe", "--tags", "--exact-match", sha])
    except subprocess.CalledProcessError:
        return []


def parse_version(tag, scope=None):
    prefix = ""
    if scope is not None:
        prefix = scope + "_"
    sv_parser = re.compile(r"^" + prefix + r"(\d+).(\d+).(\d+)$")
    match = sv_parser.match(tag)
    if match:
        return Version(major=int(match.group(1)),
                       minor=int(match.group(2)),
                       patch=int(match.group(3)))
    raise ValueError("Not a version")


def version_from_tags(tags, scope=None):
    for tag in tags:
        try:
            return parse_version(tag, scope)
        except ValueError:
            pass
    return None


def get_commits(scope=None):
    # Guard against empty repositories.
    count = int(run(["git", "rev-list", "--all", "--count"])[0])
    if count < 1:
        return []

    results = []
    command = ["git", "log", "--pretty=format:%H:%s"]
    try:
        commits = run(command)
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr.decode("utf-8"))
        exit(1)
    for c in commits:
        sha, message = c.split(":", 1)
        tags = get_tags(sha)
        commit = Commit(sha, parse_message(message), tags, version_from_tags(tags, scope))
        results.append(commit)
    return results


def parse_message(message):
    cc_parser = re.compile(r"^(.+?)(\((.+?)\))?(\!)?:(.+)$")
    match = cc_parser.match(message)
    if match is not None:
        (cc_type, cc_scope, cc_break, cc_description) = (match.group(1), match.group(3), match.group(4), match.group(5))
        try:
            return Message(type=Type(cc_type),
                           scope=cc_scope,
                           breaking_change=(cc_break == "!"),
                           description=cc_description.strip())
        except ValueError:
            pass
    return Message(type=Type.UNKNOWN,
                   scope=None,
                   breaking_change=False,
                   description=message.strip())


def format_messages(messages, section):
    result = ""
    result = result + f"**{section}**\n\n"
    for message in reversed(messages):
        result = result + f"- {message.description}"
        if message.scope is not None:
            result = result + f" ({message.scope})"
        result = result + "\n"
    return result


def format_changes(changes):
    result = ""
    sections = collections.defaultdict(list)
    for commit in changes:
        sections[TYPE_TO_SECTION[commit.message.type]].append(commit.message)
    content = []
    if "Changes" in sections:
        content.append(format_messages(sections["Changes"], "Changes"))
    if "Fixes" in sections:
        content.append(format_messages(sections["Fixes"], "Fixes"))
    return "\n".join(content)


def format_release(release):
    result = f"# {release.version}"
    if not release.is_released:
        result = result + " (Unreleased)"
    result = result + "\n\n"
    result = result + format_changes(release.changes)
    return result


def format_releases(releases):
    content = [format_release(release) for release in releases]
    return "\n".join(content)
    return result


def resolve_scope(options):
    if options.scope is not None:
        return options.scope
    try:
        return options.legacy_scope
    except AttributeError:
        return None


@cli.command("version", help="output the current version as determined by taking the the most recent version tag and applying any subsequent changes; if there have been no changes since the most recent version tag, this will output the version of the most recent tag", arguments=[
    cli.Argument("--scope", help="scope to be used in tags and commit messages"),
    cli.Argument("--released", action="store_true", default=False, help="scope to be used in tags and commit messages"),
])
def command_version(options):
    history = History(path=os.getcwd(), scope=resolve_scope(options), skip_unreleased=options.released)
    print(history.releases[0].version)


@cli.command("release", help="tag the commit as a new release", arguments=[
    cli.Argument("--scope", help="scope to be used in tags and commit messages"),
    cli.Argument("--skip-if-empty", action="store_true", default=False, help="exit cleanly if there are no changes to release"),
    cli.Argument("--command", help="additional command to run to perform during the release; if the command fails, the release will be rolled back"),
    cli.Argument("--push", action="store_true", default=False, help="push the newly created tag"),
    cli.Argument("--dry-run", action="store_true", default=False, help="perform a dry run, only logging the operations that would be performed"),
])
def command_release(options):
    history = History(path=os.getcwd(), scope=resolve_scope(options))
    releases = history.releases
    if releases[0].is_released or releases[0].is_empty:
        # There aren't any unreleased versions.
        if options.skip_if_empty:
            exit()
        logging.error("No versions to release.")
        exit(1)
    version = releases[0].version
    logging.info("Releasing %s...", version)
    tag = str(version)
    if options.scope is not None:
        tag = f"{options.scope}_{tag}"
    logging.info("Creating tag '%s'...", tag)
    run(["git", "tag", tag], dry_run=options.dry_run)

    title = str(version)
    if options.scope is not None:
        title = f"{options.scope} {title}"

    if options.push:
        logging.info("Pushing tag '%s'...", tag)
        run(["git", "push", "origin", tag], dry_run=options.dry_run)

    if options.command is not None:
        logging.info("Running command...")
        success = True

        notes = format_changes(releases[0].changes)

        # Create a temporary directory containing the notes.
        with tempfile.NamedTemporaryFile() as notes_file:
            with open(notes_file.name, "w") as fh:
                fh.write(notes)

            # Set up the environment.
            env = copy.deepcopy(os.environ)
            env['CHANGES_TITLE'] = title
            env['CHANGES_VERSION'] = str(version)
            env['CHANGES_TAG'] = tag
            env['CHANGES_NOTES'] = notes
            env['CHANGES_NOTES_FILE'] = notes_file.name

            # Run the command.
            if options.dry_run:
                logging.info(options.command)
            else:
                result = subprocess.run(options.command, shell=True, capture_output=True, env=env)
                try:
                    result.check_returncode()
                    logging.info(result.stdout.decode("utf-8").strip())
                except subprocess.CalledProcessError as e:
                    logging.error("Release command failed with error '%s'; reverting release.", e.stderr.decode("utf-8").strip())
                    run(["git", "tag", "-d", tag])
                    run(["git", "push", "origin", f":{tag}"])
                    success = False

        if not success:
            exit(1)

    logging.info("Done.")


@cli.command("notes", help="output the release notes", arguments=[
    cli.Argument("--scope", help="filter the release notes to the given scope"),
    cli.Argument("--skip-unreleased", action="store_true", help="skip unreleased versions"),
    cli.Argument("--history", help="file containing changes for versions not adhereing to Conventional Commits"),
    cli.Argument("--released", action="store_true", default=False, help="show only released versions; display the most recent released version, or all versions if the '--all' flag is specified"),
    cli.Argument("--all", action="store_true", default=False, help="output release notes for all versions"),
])
def command_notes(options):
    history = History(path=os.getcwd(), history=options.history, scope=resolve_scope(options), skip_unreleased=options.released)
    if options.all:
        print(history.format_changes(), end="")
    else:
        print(format_changes(history.releases[0].changes), end="")


DESCRIPTION = """

Lightweight and (hopefully) unopinionated tool for managing Semantic Versioning using Conventional Commits.

Changes currently a number of commands that can be assembled in whatever way fits your workflow.
"""

EPILOG = """
You can find out more about Conventional Commits and Semantic Versioning at the following links:

- Conventional Commits: https://www.conventionalcommits.org
- Semantic Versioning: https://semver.org
"""

def main():
    verbose = '--verbose' in sys.argv[1:] or '-v' in sys.argv[1:]
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="[%(levelname)s] %(message)s")
    parser = cli.CommandParser(description=DESCRIPTION, epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help="show verbose output")
    if "--scope" in sys.argv:
        parser.add_argument("--scope", dest="legacy_scope", help="scope to be used in tags and commit messages")
    parser.run()


if __name__ == "__main__":
    main()
