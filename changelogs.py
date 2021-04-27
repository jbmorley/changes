#!/usr/bin/env python3

import argparse
import re
import subprocess


class Version(object):

    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

    def bump_major(self):
        self.major = self.major + 1
        self.minor = 0
        self.patch = 0

    def bump_minor(self):
        self.minor = self.minor + 1
        self.patch = 0

    def bump_patch(self):
        self.patch = self.patch + 1

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


def run(command):
    result = subprocess.check_output(command, stderr=subprocess.PIPE)
    lines = result.decode("utf-8").strip().split("\n")
    return lines


def commits(ref):
    return run(["git", "log", "--pretty=format:%H", ref])


def get_tags(sha):
    try:
        return run(["git", "describe", "--tags", "--exact-match", sha])
    except subprocess.CalledProcessError:
        return []


def tags(ref):
    result = []
    for commit in commits(ref):
        result.append(get_tags(commit))
    return result


def latest_version(ref):
    # Iterate over the tags in the current branch and stop at the first valid version.
    sv_parser = re.compile(r"^(\d+).(\d+).(\d+)$")
    for tag_list in tags(ref):
        found = False
        for tag in tag_list:
            match = sv_parser.match(tag)
            if match:
                return Version(major=int(match.group(1)),
                               minor=int(match.group(2)),
                               patch=int(match.group(3)))
    return Version()


OPERATIONS = {
    "BREAKING CHANGE": lambda x: x.bump_major(),
    "feat": lambda x: x.bump_minor(),
    "fix": lambda x: x.bump_patch(),
}


class Commit(object):

    def __init__(self, sha, message, tags):
        self.sha = sha
        self.message = message
        self.tags = tags


def get_commit(sha):
    details = run(["git", "log", "--pretty=format:%H:%s", "--max-count", "1", sha])[0]
    sha, message = details.split(":", 1)
    return Commit(sha, message, get_tags(sha))


def get_commits(ref):
    results = []
    commits = run(["git", "log", "--pretty=format:%H:%s", ref])
    for commit in commits:
        sha, message = commit.split(":", 1)
        results.append(Commit(sha, message, get_tags(sha)))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", help="namespace to be used in tags and commit messages")
    parser.add_argument("--skip-tags", action="store_true", default=False, help="ignore existing tags")
    options = parser.parse_args()

    cc_parser = re.compile(r"^(.+?):.+")

    for commit in get_commits("main"):
        print(commit)
        print(commit.tags)
    exit()



    # TODO: Support namespaces.
    version = Version()
    if not options.skip_tags:
        version = latest_version("main")
    print(f"Starting version = {version}")

    logs = reversed(subprocess.check_output(["git", "log", "--pretty=format:%s"]).decode("utf-8").split("\n"))
    for log in logs:
        result = cc_parser.match(log)
        if result:
            commit_type = result.group(1)
            operation = OPERATIONS[commit_type]
            operation(version)
            print(f"{version} ({commit_type})")
        else:
            print("Not sure what to do with this log line?")
        print(log)






if __name__ == "__main__":
    main()