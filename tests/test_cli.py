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

from common import Commit, EmptyCommit, Release, Repository, Tag

common.configure_path()


class CLITestCase(unittest.TestCase):

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

    def test_current_version_raw_output(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
            ])
            self.assertEqual(repository.changes(["version"]), "0.0.0\n")

    def test_current_version(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("inital commit"),
                Tag("0.2.0")
            ])
            self.assertEqual(repository.changes_version(), "0.2.0")
            repository.perform([
                EmptyCommit("ignored commit"),
            ])
            self.assertEqual(repository.changes_version(), "0.2.0")
            repository.perform([
                EmptyCommit("fix: this fix should update the patch version"),
            ])
            self.assertEqual(repository.changes_version(), "0.2.1")
            repository.perform([
                EmptyCommit("feat: this feature should update the minor verison"),
            ])
            self.assertEqual(repository.changes_version(), "0.3.0")
            repository.perform([
                EmptyCommit("feat!: this break should update the major verison"),
            ])
            self.assertEqual(repository.changes_version(), "1.0.0")

    def test_current_version_no_changes(self):
        with Repository() as repository:
            self.assertEqual(repository.changes_version(), "0.0.0")

    def test_current_version_multiple_changes_yield_single_increment(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("inital commit"),
                Tag("0.1.0")
            ])
            self.assertEqual(repository.changes_version(), "0.1.0")
            repository.perform([
                EmptyCommit("fix: this fix should update the patch version"),
                EmptyCommit("fix: this fix should not update the patch version"),
            ])
            self.assertEqual(repository.changes_version(), "0.1.1")
            repository.perform([
                EmptyCommit("feat: this feat should update the minor version"),
                EmptyCommit("feat: this feat should not update the minor version"),
            ])
            self.assertEqual(repository.changes_version(), "0.2.0")
            repository.perform([
                EmptyCommit("feat!: this breaking change should update the major version"),
                EmptyCommit("feat!: this breaking change should not update the major version"),
            ])
            self.assertEqual(repository.changes_version(), "1.0.0")

    def test_current_version_with_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("a_1.0.0"),
            ])
            self.assertEqual(repository.changes_version(), "0.0.0")
            self.assertEqual(repository.changes_version(scope="a"), "1.0.0")
            self.assertEqual(repository.changes_version(scope="b"), "0.0.0")


    def test_current_version_with_legacy_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("a_1.0.0"),
            ])
            self.assertEqual(repository.changes(["version"]), "0.0.0\n")
            self.assertEqual(repository.changes(["--scope", "a", "version"]), "1.0.0\n")
            self.assertEqual(repository.changes(["--scope", "b", "version"]), "0.0.0\n")


    def test_exclamation_mark_indicates_breaking_change(self):
        with Repository()as repository:
            repository.perform([
                EmptyCommit("feat!: Breaking feat should increment major version"),
            ])
            self.assertEqual(repository.changes_version(), "1.0.0")
            repository.changes_release()
            repository.perform([
                EmptyCommit("fix!: Breaking fix should increment major version"),
            ])
            self.assertEqual(repository.changes_version(), "2.0.0")
            repository.perform([
                EmptyCommit("wibble!: Unknown breaking type should do nothing"),
                EmptyCommit("ci!: Unknown ignored type should do nothing"),
            ])
            self.assertEqual(repository.changes_version(), "2.0.0")

    def test_released_version_raw_output(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.6.12"),
            ])
            self.assertEqual(repository.changes(["version", "--released"]), "1.6.12\n")

    def test_released_version_no_tag_fails(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["released-version"])

    def test_released_version(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("2.1.3"),
            ])
            self.assertEqual(repository.changes_version(released=True), "2.1.3")
            repository.perform([
                EmptyCommit("fix: this fix should not affect the released version"),
                EmptyCommit("feat: this feat should not affect the released version"),
                EmptyCommit("feat!: this breaking change should not affect the released version"),
            ])
            self.assertEqual(repository.changes_version(released=True), "2.1.3")

    def test_release_fails_empty_repository(self):
        with Repository() as repository:
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes_release()

    def test_release_fails_without_changes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit with no changes"),
                Tag("0.1.1")
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes_release()

    def test_release_fails_without_changes_or_previous_release(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit with no changes"),
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes_release()

    def test_current_notes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.0.0")
            ])
            self.assertEqual(repository.current_notes(), "")
            repository.perform([
                EmptyCommit("fix: Doesn't crash"),
                EmptyCommit("fix: Works"),
            ])
            self.assertEqual(repository.current_notes(),
"""**Fixes**

- Doesn't crash
- Works
""")
            repository.perform([
                EmptyCommit("feat: New Shiny"),
            ])
            self.assertEqual(repository.current_notes(),
"""**Changes**

- New Shiny

**Fixes**

- Doesn't crash
- Works
""")
            repository.changes_release()
            self.assertEqual(repository.current_notes(),
"""**Changes**

- New Shiny

**Fixes**

- Doesn't crash
- Works
""")
            repository.perform([
                EmptyCommit("feat: More Shiny"),
            ])
            self.assertEqual(repository.current_notes(),
"""**Changes**

- More Shiny
""")

    def test_all_changes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: Initial commit"),
                Release(),
                EmptyCommit("fix: Fix something"),
                EmptyCommit("fix: Fix something else"),
                Release(),
                EmptyCommit("fix!: Fix something breaking compatibility"),
                Release(),
                EmptyCommit("feat: Unreleased feature"),
            ])
            self.assertEqual(repository.changes_all_changes(),
"""# 1.1.0 (Unreleased)

**Changes**

- Unreleased feature

# 1.0.0

**Fixes**

- Fix something breaking compatibility

# 0.1.1

**Fixes**

- Fix something
- Fix something else

# 0.1.0

**Changes**

- Initial commit
""")

    def test_all_changes_skip_unreleased(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: Initial commit"),
                Release(),
                EmptyCommit("fix: Fix something"),
                EmptyCommit("fix: Fix something else"),
                Release(),
                EmptyCommit("fix!: Fix something breaking compatibility"),
                Release(),
                EmptyCommit("feat: Unreleased feature"),
            ])
            self.assertEqual(repository.changes_all_changes(skip_unreleased=True),
"""# 1.0.0

**Fixes**

- Fix something breaking compatibility

# 0.1.1

**Fixes**

- Fix something
- Fix something else

# 0.1.0

**Changes**

- Initial commit
""")

    def test_release_notes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: Initial commit"),
                Release(),
                EmptyCommit("fix: Fix something"),
                EmptyCommit("fix: Fix something else"),
                Release(),
                EmptyCommit("fix!: Fix something breaking compatibility"),
                Release(),
                EmptyCommit("feat: Unreleased feature"),
            ])
            self.assertEqual(repository.changes_release_notes(),
"""# 1.0.0

**Fixes**

- Fix something breaking compatibility

# 0.1.1

**Fixes**

- Fix something
- Fix something else

# 0.1.0

**Changes**

- Initial commit
""")

    def test_release_notes_additional_history_preserves_ordering(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
            ])
            repository.write_yaml("history.yaml", {
                "2.0.0": [
                    "feat: Baz",
                    "fix: Foo",
                    "feat: Bar",
                ]
            })
            self.assertEqual(repository.changes_all_changes(skip_unreleased=True, history="history.yaml"),
"""# 2.0.0

**Changes**

- Baz
- Bar

**Fixes**

- Foo
""")

    def test_release_notes_additional_history_merges_cahnges(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.10.1"),
                EmptyCommit("feat: New and exciting"), # TODO: Why didn't the breaking change work??
            ])
            repository.write_yaml("history.yaml", {
                "1.11.0": [
                    "feat: Baz",
                    "fix: Foo",
                    "feat: Bar",
                ]
            })
            self.assertEqual(repository.changes_all_changes(history="history.yaml"),
"""# 1.11.0 (Unreleased)

**Changes**

- Baz
- Bar
- New and exciting

**Fixes**

- Foo

# 1.10.1

""")


if __name__ == '__main__':
    unittest.main()
