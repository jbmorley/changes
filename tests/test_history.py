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
import subprocess
import unittest

import common

common.configure_path()

import changes

from changes import Change, History, Message, Type, Version
from common import EmptyCommit, Repository, Tag


class HistoryTestCase(unittest.TestCase):

    # TODO: Remember to test the scope.
    # TODO: Test overlapping releases.
    # TODO: Check ignores wrong tags
    # TODO: Check fails with invalid config.
    # TODO: Check the ordering of the versions.
    # TODO: Ensure the output ordering matches the input ordering for the changes
    # TODO: Consider what happens with versions
    # TODO: Test the augmentation/merge operation
    # TODO: Object level tests for the imported history (perhaps when it's a separate method?)
    # TODO: Single command for release notes
    # TODO: Validate the schema of the history input file.

    def test_override(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("21.0.0"),
            ])
            history = History(path=repository.path)
            self.assertEqual(len(history.releases), 1)
            repository.write_file("history.yaml", """
"1.0.0": []
"2.0.0":
- "feat: New feature"
            """)
            history = History(path=repository.path, history=os.path.join(repository.path, "history.yaml"))
            self.assertEqual(len(history.releases), 3)
            versions = [str(release.version) for release in history.releases]
            self.assertEqual(versions, ["21.0.0", "2.0.0", "1.0.0"])

            repository.write_yaml("history.yaml", {
                "2.0.0": [
                    "feat: New feature",
                ]
            })
            history = History(path=repository.path, history=os.path.join(repository.path, "history.yaml"))
            self.assertEqual(len(history.releases), 2)
            versions = [str(release.version) for release in history.releases]
            self.assertEqual(versions, ["21.0.0", "2.0.0"])
            self.assertEqual(history.releases[1].changes, [Change(Message(type=Type.FEATURE, scope=None, breaking_change=False, description="New feature"))])
            self.assertNotEqual(history.releases[1].changes, [Change(Message(type=Type.FIX, scope=None, breaking_change=False, description="New feature"))])


if __name__ == '__main__':
    unittest.main()
