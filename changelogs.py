#!/usr/bin/env python

import argparse
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


def main():
    parser = argparse.ArgumentParser()
    options = parser.parse_args()

    logs = subprocess.check_output(["git", "log", "--pretty=format:%s"]).decode("utf-8").split("\n")
    print(logs)



if __name__ == "__main__":
    main()