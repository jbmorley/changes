#!/usr/bin/env python3

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

import logging
import os
import subprocess
import sys
import tempfile
import unittest

from . import common

from .common import Commit, EmptyCommit, Release, Repository, Tag


# TODO: Test current version.
# TODO: Test additive changes.
# TODO: Test resetting changes.
# TODO: Write tests for multiple pre-releases with scopes and different versions!

class CLITestCase(unittest.TestCase):

    def test_version_raw_output(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
            ])
            self.assertEqual(repository.changes(["version"]), "0.0.0\n")

    def test_version(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("inital commit"),
                Tag("0.2.0")
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.2.0")
            repository.perform([
                EmptyCommit("ignored commit"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.2.0")
            repository.perform([
                EmptyCommit("fix: this fix should update the patch version"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.2.1")
            repository.perform([
                EmptyCommit("feat: this feature should update the minor verison"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.3.0")
            repository.perform([
                EmptyCommit("feat!: this break should update the major verison"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "1.0.0")

    def test_version_no_changes(self):
        with Repository() as repository:
            self.assertEqual(repository.changes(["version"]).strip(), "0.0.0")

    def test_version_multiple_changes_yield_single_increment(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("inital commit"),
                Tag("0.1.0")
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.1.0")
            repository.perform([
                EmptyCommit("fix: this fix should update the patch version"),
                EmptyCommit("fix: this fix should not update the patch version"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.1.1")
            repository.perform([
                EmptyCommit("feat: this feat should update the minor version"),
                EmptyCommit("feat: this feat should not update the minor version"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.2.0")
            repository.perform([
                EmptyCommit("feat!: this breaking change should update the major version"),
                EmptyCommit("feat!: this breaking change should not update the major version"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "1.0.0")

    def test_version_with_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("a_1.0.0"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "0.0.0")
            self.assertEqual(repository.changes(["version", "--scope", "a"]).strip(), "1.0.0")
            self.assertEqual(repository.changes(["version", "--scope", "b"]).strip(), "0.0.0")

    def test_version_with_legacy_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("a_1.0.0"),
            ])
            self.assertEqual(repository.changes(["version"]), "0.0.0\n")
            self.assertEqual(repository.changes(["--scope", "a", "version"]), "1.0.0\n")
            self.assertEqual(repository.changes(["--scope", "b", "version"]), "0.0.0\n")

    def test_version_multiple_tags_unknown(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.0.0"),
                Tag("fromage"),
            ])
            self.assertEqual(repository.changes(["version"]), "1.0.0\n")

    def test_version_multiple_tags_unknown_first(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1"),
                Tag("1.1.1"),
            ])
            self.assertEqual(repository.changes(["version"]), "1.1.1\n")

    def test_version_pre_release(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.0.0"),
            ])
            self.assertEqual(repository.changes(["version"]), "1.0.0\n")
            self.assertEqual(repository.changes(["version", "--pre-release"]), "1.0.0\n")
            repository.perform([
                EmptyCommit("feat: this feat should update the minor version and pre-release version"),
                EmptyCommit("feat: this feat should not update the minor version or pre-release version"),
            ])
            self.assertEqual(repository.changes(["version"]), "1.1.0\n")
            self.assertEqual(repository.changes(["version", "--pre-release"]), "1.1.0-rc\n")
            self.assertEqual(repository.changes(["version", "--pre-release", "--pre-release-prefix", "alpha"]), "1.1.0-alpha\n")
            repository.perform([
                Tag("1.1.0-rc"),
                EmptyCommit("feat: this feat should not update the minor version but should update the commited pre-release version"),
            ])
            self.assertEqual(repository.changes(["version"]), "1.1.0\n")
            self.assertEqual(repository.changes(["version", "--pre-release"]), "1.1.0-rc.1\n")
            self.assertEqual(repository.changes(["version", "--pre-release", "--pre-release-prefix", "alpha"]), "1.1.0-alpha\n")

    def test_version_on_clone(self):
        with Repository() as remote, tempfile.TemporaryDirectory() as temporary_directory:
            remote.perform([
                EmptyCommit("feat: feature"),
            ])
            common.run(["git", "clone", remote.path, "clone"], temporary_directory)
            repository_path = os.path.join(temporary_directory, "clone")
            result = common.run(["changes", "version"], repository_path)
            result.check_returncode()
            self.assertEqual(result.stdout.decode("utf-8").strip(), "0.1.0")

    def test_fails_on_shallow_clone(self):
        with Repository() as remote, tempfile.TemporaryDirectory() as temporary_directory:
            remote.perform([
                EmptyCommit("feat: feature"),
                EmptyCommit("fix: oops"),
            ])
            common.run(["git", "clone", "--depth", "1", "file://" + remote.path, "clone"], temporary_directory)
            repository_path = os.path.join(temporary_directory, "clone")

            result = common.run(["changes", "version"], repository_path)
            with self.assertRaises(subprocess.CalledProcessError):
                result.check_returncode()
            self.assertEqual(result.stderr.decode("utf-8").strip(), "[ERROR] Unable to determine change history for shallow clones.")

            result = common.run(["changes", "notes"], repository_path)
            with self.assertRaises(subprocess.CalledProcessError):
                result.check_returncode()
            self.assertEqual(result.stderr.decode("utf-8").strip(), "[ERROR] Unable to determine change history for shallow clones.")

            result = common.run(["changes", "release"], repository_path)
            with self.assertRaises(subprocess.CalledProcessError):
                result.check_returncode()
            self.assertEqual(result.stderr.decode("utf-8").strip(), "[ERROR] Unable to determine change history for shallow clones.")

    def test_exclamation_mark_indicates_breaking_change(self):
        with Repository()as repository:
            repository.perform([
                EmptyCommit("feat!: Breaking feat should increment major version"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "1.0.0")
            repository.changes(["release"])
            repository.perform([
                EmptyCommit("fix!: Breaking fix should increment major version"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "2.0.0")
            repository.perform([
                EmptyCommit("wibble!: Unknown breaking type should do nothing"),
                EmptyCommit("ci!: Unknown ignored type should do nothing"),
            ])
            self.assertEqual(repository.changes(["version"]).strip(), "2.0.0")

    def test_version_released_raw_output(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.6.12"),
            ])
            self.assertEqual(repository.changes(["version", "--released"]), "1.6.12\n")

    def test_version_released_no_tag_fails(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["version", "--released"])

    def test_version_released(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("2.1.3"),
            ])
            self.assertEqual(repository.changes(["version", "--released"]).strip(), "2.1.3")
            repository.perform([
                EmptyCommit("fix: this fix should not affect the released version"),
                EmptyCommit("feat: this feat should not affect the released version"),
                EmptyCommit("feat!: this breaking change should not affect the released version"),
            ])
            self.assertEqual(repository.changes(["version", "--released"]).strip(), "2.1.3")

    def test_release_tag(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            repository.changes(["release"])
            self.assertEqual(repository.tag(), ["0.1.0"])

    def test_release_tag_push(self):
        with Repository() as repository, Repository() as remote:
            repository.git(["remote", "add", "origin", remote.path])
            self.assertEqual(remote.tag(), [])
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            repository.changes(["release", "--push"])
            self.assertEqual(repository.tag(), ["0.1.0"])
            self.assertEqual(remote.tag(), ["0.1.0"])

    def test_release_tag_with_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat(cheese): feature"),
            ])
            repository.changes(["release", "--scope", "cheese"])
            self.assertEqual(repository.tag(), ["cheese_0.1.0"])
            repository.perform([
                EmptyCommit("feat: another feature"),
            ])
            repository.changes(["release"])
            self.assertEqual(sorted(repository.tag()), ["0.1.0", "cheese_0.1.0"])
            repository.perform([
                EmptyCommit("fix(cheese): fixed something"),
            ])
            repository.changes(["--scope", "cheese", "release"])
            self.assertEqual(sorted(repository.tag()), ["0.1.0", "cheese_0.1.0", "cheese_0.2.0"])

    def test_release_tag_cleanup_on_failure(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["release", "--command", "exit 1"])
            self.assertEqual(repository.tag(), [])

    def test_release_tag_push_cleanup_on_failure(self):
        with Repository() as repository, Repository() as remote:
            repository.git(["remote", "add", "origin", remote.path])
            self.assertEqual(remote.tag(), [])
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["release", "--push", "--command", "exit 1"])
            self.assertEqual(repository.tag(), [])
            self.assertEqual(remote.tag(), [])

    def test_release_fails_empty_repository(self):
        with Repository() as repository:
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["release"])

    def test_release_fails_without_changes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit with no changes"),
                Tag("0.1.1")
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["release"])

    def test_release_fails_without_changes_or_previous_release(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit with no changes"),
            ])
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["release"])

    def test_release_command_default_interpreter(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            repository.changes(["release", "--command", "ps h -p $$ -o args='' | cut -f1 -d' ' > output.txt"])
            self.assertEqual(repository.read_file("output.txt").strip(), "/bin/sh")

    def test_release_command_bash_script(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            script_path = repository.write_file("script.sh", """#!/bin/bash
ps h -p $$ -o args='' | cut -f1 -d' ' > output.txt
""", mode=0o744)
            repository.changes(["release", "--command", script_path])
            self.assertEqual(repository.read_file("output.txt").strip(), "/bin/bash")

    def test_release_command_bash_script_correct_echo(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            script_path = repository.write_bash_script("script.sh", "echo -n Foo > output.txt")
            repository.changes(["release", "--command", script_path])
            self.assertEqual(repository.read_file("output.txt"), "Foo")

    def test_release_command_and_exec_fails(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            script_path = repository.write_bash_script("script.sh", "echo -n Foo > output.txt")
            with self.assertRaises(subprocess.CalledProcessError):
                repository.changes(["release", "--command", script_path, "--exec", script_path])

    def test_release_exec_relative_path(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            script_path = repository.write_bash_script("script.sh", "echo -n Foo > output.txt")
            logging.debug("Script path '%s'", script_path)
            repository.changes(["release", "--exec", "script.sh"])
            self.assertEqual(repository.read_file("output.txt"), "Foo")

    def test_release_exec_absolute_path(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: feature"),
            ])
            script_path = repository.write_bash_script("script.sh", "echo -n Foo > output.txt")
            repository.changes(["release", "--exec", script_path])
            self.assertEqual(repository.read_file("output.txt"), "Foo")

    def test_release_command_environment_version(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["release", "--command", "echo $CHANGES_VERSION >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"), "0.1.0\n")

    def test_release_exec_environment_version(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            script_path = repository.write_bash_script("script.sh", "echo -n $CHANGES_VERSION > output.txt")
            repository.changes(["release", "--exec", script_path])
            self.assertEqual(repository.read_file("output.txt"), "0.1.0")

    def test_release_command_environment_prerelease(self):
        with Repository() as repository:
            repository.perform([EmptyCommit("feat: initial commit")])
            script_path = repository.write_bash_script("script.sh", """
if $CHANGES_INITIAL_DEVELOPMENT ; then
echo -n "prerelease" > output.txt
else
echo -n "release" > output.txt
fi
""")
            repository.changes(["release", "--command", script_path])
            self.assertEqual(repository.read_file("output.txt"), "prerelease")

            repository.perform([EmptyCommit("fix: minor fix")])
            repository.changes(["release", "--command", script_path])
            self.assertEqual(repository.read_file("output.txt"), "prerelease")

            repository.perform([EmptyCommit("feat!: initial release")])
            repository.changes(["release", "--command", script_path])
            self.assertEqual(repository.read_file("output.txt"), "release")

    def test_release_command_environment_title(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["release", "--command", "echo $CHANGES_TITLE >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"), "0.1.0\n")

    def test_release_command_environment_tag(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["release", "--command", "echo $CHANGES_TAG >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"), "0.1.0\n")

    def test_release_command_environment_tag_with_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["release", "--scope", "scope", "--command", "echo $CHANGES_TAG >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"), "scope_0.1.0\n")

    def test_release_command_environment_tag_with_scope_legacy_argument(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["--scope", "scope", "release", "--command", "echo $CHANGES_TAG >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"), "scope_0.1.0\n")

    def test_release_command_environment_notes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["release", "--command", "echo \"$CHANGES_NOTES\" >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"),
"""**Changes**

- New feature

""")
            repository.perform([
                EmptyCommit("fix: Improved something"),
            ])
            repository.changes(["release", "--command", "echo \"$CHANGES_NOTES\" >> output.txt"])
            self.assertEqual(repository.read_file("output.txt"),
"""**Changes**

- New feature

**Fixes**

- Improved something

""")

    def test_release_command_environment_notes_changes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
            ])
            repository.changes(["release", "--command", "cat \"$CHANGES_NOTES_FILE\" > output.txt"])
            self.assertEqual(repository.read_file("output.txt"),
"""**Changes**

- New feature
""")

    def test_release_command_environment_notes_changes_and_fixes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
                EmptyCommit("fix: Improved something"),
            ])
            repository.changes(["release", "--command", "cat \"$CHANGES_NOTES_FILE\" > output.txt"])
            self.assertEqual(repository.read_file("output.txt"),
"""**Changes**

- New feature

**Fixes**

- Improved something
""")

    def test_release_command_environment_notes_template(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
                EmptyCommit("fix: Improved something"),
            ])
            repository.write_file("template.txt", "{{ releases | length }}")
            repository.changes(["release", "--command", "cat \"$CHANGES_NOTES_FILE\" > output.txt", "--template", "template.txt"])
            self.assertEqual(repository.read_file("output.txt"), "1\n")

    def test_release_command_single_argument(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
                EmptyCommit("fix: Improved something"),
            ])
            repository.changes(["release", "--command", "echo \"$@\" > output.txt", "a"])
            self.assertEqual(repository.read_file("output.txt"), "a\n")

    def test_release_command_multiple_arguments(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("feat: New feature"),
                EmptyCommit("fix: Improved something"),
            ])
            script_path = repository.write_bash_script("count.sh", """printf '%s\n' "$@" > output.txt""")
            repository.changes(["release", "--command", f'{script_path} "$@"', "a", "b", "c d e"])
            self.assertEqual(repository.read_file("output.txt"), "a\nb\nc d e\n")

    def test_current_notes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.0.0")
            ])
            self.assertEqual(repository.changes(["notes"]), "\n")
            repository.perform([
                EmptyCommit("fix: Doesn't crash"),
                EmptyCommit("fix: Works"),
            ])
            self.assertEqual(repository.changes(["notes"]),
"""**Fixes**

- Doesn't crash
- Works
""")
            repository.perform([
                EmptyCommit("feat: New Shiny"),
            ])
            self.assertEqual(repository.changes(["notes"]),
"""**Changes**

- New Shiny

**Fixes**

- Doesn't crash
- Works
""")
            repository.changes(["release"])
            self.assertEqual(repository.changes(["notes"]),
"""**Changes**

- New Shiny

**Fixes**

- Doesn't crash
- Works
""")
            repository.perform([
                EmptyCommit("feat: More Shiny"),
            ])
            self.assertEqual(repository.changes(["notes"]),
"""**Changes**

- More Shiny
""")

    def test_notes_released(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.0.0")
            ])
            self.assertEqual(repository.changes(["notes"]), "\n")
            repository.perform([
                EmptyCommit("fix: Doesn't crash"),
                EmptyCommit("fix: Works"),
            ])
            self.assertEqual(repository.changes(["notes", "--released"]), "\n")
            repository.changes(["release"])
            self.assertEqual(repository.changes(["notes", "--released"]),
"""**Fixes**

- Doesn't crash
- Works
""")
            repository.perform([
                EmptyCommit("feat: More Shiny"),
            ])
            self.assertEqual(repository.changes(["notes", "--released"]),
"""**Fixes**

- Doesn't crash
- Works
""")

    def test_notes_all(self):
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
            self.assertEqual(repository.changes(["notes", "--all"]),
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

    def test_notes_all_released(self):
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
            self.assertEqual(repository.changes(["notes", "--all", "--released"]),
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

    def test_notes(self):
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
            self.assertEqual(repository.changes(["notes", "--all", "--released"]),
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

    def test_notes_template(self):
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
            repository.write_file("template.txt", "{{ releases | length }}")
            self.assertEqual(repository.changes(["notes", "--all", "--released", "--template", "template.txt"]), "3\n")

    def test_notes_additional_history_preserves_ordering(self):
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
            self.assertEqual(repository.changes(["notes", "--released", "--all", "--history", "history.yaml"]),
"""# 2.0.0

**Changes**

- Baz
- Bar

**Fixes**

- Foo
""")

    def test_notes_additional_history_merges_changes(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("1.10.1"),
                EmptyCommit("feat: New and exciting"),
            ])
            repository.write_yaml("history.yaml", {
                "1.11.0": [
                    "feat: Baz",
                    "fix: Foo",
                    "feat: Bar",
                ]
            })
            self.assertEqual(repository.changes(["notes", "--all", "--history", "history.yaml"]),
"""# 1.11.0 (Unreleased)

**Changes**

- Baz
- Bar
- New and exciting

**Fixes**

- Foo

# 1.10.1
""")

    def test_notes_additional_history_ignoring_scope(self):
        with Repository() as repository:
            repository.perform([
                EmptyCommit("initial commit"),
                Tag("macOS_1.0.0"),
            ])
            repository.write_yaml("history.yaml", {
                "macOS_1.0.1": [
                    "feat: Baz",
                    "fix: Foo",
                    "feat: Bar",
                ],
                "1.0.0": [
                    "feat!: Initial release"
                ]
            })
            self.assertEqual(repository.changes(["notes", "--all", "--history", "history.yaml", "--scope", "macOS"]),
"""# 1.0.1

**Changes**

- Baz
- Bar

**Fixes**

- Foo

# 1.0.0
""")

            self.assertEqual(repository.changes(["notes", "--all", "--released", "--history", "history.yaml"]),
"""# 1.0.0

**Changes**

- Initial release
""")


if __name__ == '__main__':
    unittest.main()
