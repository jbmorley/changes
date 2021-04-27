#!/usr/bin/env python3

import argparse
import re
import subprocess


class Version(object):

    def __init__(self):
        self.major = 0
        self.minor = 0
        self.patch = 0

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


def main():
    parser = argparse.ArgumentParser()
    options = parser.parse_args()

    version = Version()

    parser = re.compile(r"^(.+?):.+")

    operations = {
        "BREAKING CHANGE": lambda x: x.bump_major(),
        "feat": lambda x: x.bump_minor(),
        "fix": lambda x: x.bump_patch(),
    }

    logs = reversed(subprocess.check_output(["git", "log", "--pretty=format:%s"]).decode("utf-8").split("\n"))
    for log in logs:
        result = parser.match(log)
        if result:
            commit_type = result.group(1)
            operation = operations[commit_type]
            operation(version)
            print(f"{version} ({commit_type})")
        else:
            print("Not sure what to do with this log line?")
        print(log)






if __name__ == "__main__":
    main()