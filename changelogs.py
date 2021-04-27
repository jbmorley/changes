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


def tags(ref):
    result = []
    for commit in commits(ref):
        try:
            result.append(run(["git", "describe", "--tags", "--exact-match", commit]))
        except subprocess.CalledProcessError:
            pass
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


def main():
    parser = argparse.ArgumentParser()
    options = parser.parse_args()

    cc_parser = re.compile(r"^(.+?):.+")



    # TODO: Support namespaces.
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