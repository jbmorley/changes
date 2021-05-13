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

import os
import unittest
import subprocess
import sys
import tempfile

TESTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ROOT_DIRECTORY = os.path.dirname(TESTS_DIRECTORY)

def configure_path():
    sys.path.append(ROOT_DIRECTORY)


class Chdir(object):

    def __init__(self, path):
        self.path = os.path.abspath(path)

    def __enter__(self):
        self.pwd = os.getcwd()
        os.chdir(self.path)
        return self.path

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.pwd)


class Commit(object):

    def __init__(self, message, allow_empty=False):
        self.message = message
        self.allow_empty = allow_empty

    def perform(self, repository):
        repository.commit(self.message, self.allow_empty)


class EmptyCommit(Commit):

    def __init__(self, message):
        super().__init__(message, allow_empty=True)


class Tag(object):

    def __init__(self, tagname):
        self.tagname = tagname

    def perform(self, repository):
        repository.tag(self.tagname)


class Repository(object):

    def __init__(self):
        pass

    def __enter__(self):
        self.directory = tempfile.TemporaryDirectory()
        self.directory.__enter__()
        self.init()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.directory.__exit__(exc_type, exc_value, traceback)

    def run(self, command):
        with Chdir(self.path):
            return subprocess.check_output(command).decode("utf-8")

    def git(self, arguments):
        return self.run(["git"] + arguments)

    def init(self):
        return self.git(["init", "-q"])

    def commit(self, message, allow_empty=False):
        arguments = ["commit",
                     "-m", message]
        if allow_empty:
            arguments.append("--allow-empty")
        return self.git(arguments)

    def rev_list(self, commit_id, count=False):
        arguments = ["rev-list", commit_id]
        if count:
            arguments.append("--count")
        lines = self.git(arguments).strip().split("\n")
        if count:
            return int(lines[0])
        return lines

    def tag(self, tagname=None):
        arguments = ["tag"]
        if tagname is not None:
            arguments.append(tagname)
        lines = self.git(arguments).strip().split("\n")
        lines = [line for line in lines if line]
        return lines

    def config(self, name, value):
        return self.git(["config", name, value])

    def set_user(self, name, email):
        self.config("user.name", name)
        self.config("user.email", email)

    def perform(self, operations):
        for operation in operations:
            operation.perform(self)

    @property
    def path(self):
        return self.directory.name