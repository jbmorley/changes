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

import os
import unittest

import common

from common import Commit, EmptyCommit, Repository, Tag

common.configure_path()


class CLITestCase(unittest.TestCase):

    def test_true(self):
        self.assertTrue(True)

    def test_create_repository(self):
        with Repository() as repository:
            self.assertTrue(os.path.isdir(repository.path))
            self.assertTrue(os.path.isdir(os.path.join(repository.path, ".git")))

    def test_add_commit(self):
        with Repository() as repository:
            repository.commit("commit one", allow_empty=True)
            self.assertEqual(repository.rev_list("HEAD", count=True), 1)
            repository.commit("commit two", allow_empty=True)
            self.assertEqual(repository.rev_list("HEAD", count=True), 2)

    def test_batch_commit(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("commit one"),
                EmptyCommit("commit two"),
            ])
            self.assertEqual(repository.rev_list("HEAD", count=True), 2)

    def test_tag(self):
        with Repository() as repository:
            repository.commit("commit", allow_empty=True)
            self.assertEqual(repository.rev_list("HEAD", count=True), 1)
            self.assertEqual(repository.tag(), [])
            repository.tag("1.0.0")
            self.assertEqual(repository.tag(), ["1.0.0"])

    def test_operations(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("0.1.0"),
            ])
            self.assertEqual(repository.rev_list("HEAD", count=True), 1)
            self.assertEqual(repository.tag(), ["0.1.0"])


if __name__ == '__main__':
    unittest.main()
