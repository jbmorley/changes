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

import os
import subprocess
import unittest

import common

import changes

from changes import PreRelease, Version


class VersionTestCase(unittest.TestCase):

    def test_str(self):
        self.assertEqual(str(Version()), "0.0.0")
        self.assertEqual(str(Version(0, 1, 1)), "0.1.1")
        self.assertEqual(str(Version(2, 10, 5)), "2.10.5")
        self.assertEqual(str(Version(1, 0, 0, PreRelease("rc"))), "1.0.0-rc")
        self.assertEqual(str(Version(1, 0, 0, PreRelease("rc", 0))), "1.0.0-rc")
        self.assertEqual(str(Version(1, 0, 0, PreRelease("rc", 3))), "1.0.0-rc.3")

    # TODO: Test sorting.
    # TODO: Test incrementing.
    # TODO: Test how pre-release version changes carry forwards.
    # TODO: Test parsing.
    # TODO: Test behaviour of a sequence of pre-release versions.
    # TODO: Version should be the same, but there should be pre-release details in the environment.
    # TODO: Should the title include the pre-release details?
    # TODO: The version objects imported from a history with pre-release components need to be handled very carefully.
    #       Perhaps we should only import the pre-release versions iff we're running in pre-release mode and they
    #       match the current tag?
    # TODO: What should the release notes look like?
    # TODO: Implement the release tool command

    def test_comparators(self):

        # Equals.

        self.assertEqual(Version(), Version())
        self.assertEqual(Version(1, 10, 5), Version(1, 10, 5))
        self.assertNotEqual(Version(1, 10, 5), Version(2, 10, 5))
        self.assertNotEqual(Version(1, 10, 5), Version(1, 11, 5))
        self.assertNotEqual(Version(1, 10, 5), Version(1, 10, 10))
        self.assertEqual(Version(pre_release=PreRelease("rc", 0)), Version(pre_release=PreRelease("rc", 0)))
        self.assertEqual(Version(20, 2, 10, PreRelease("rc", 0)), Version(20, 2, 10, PreRelease("rc", 0)))
        self.assertNotEqual(Version(20, 2, 10, PreRelease("rc", 0)), Version(20, 2, 10, PreRelease("alpha", 0)))
        self.assertNotEqual(Version(20, 2, 10, PreRelease("rc", 0)), Version(20, 2, 10, PreRelease("rc", 10)))
        self.assertNotEqual(Version(), Version(pre_release=PreRelease("rc", 0)))

        # Less-than.

        self.assertFalse(Version() < Version())
        self.assertTrue(Version() < Version(0, 1, 4))
        self.assertTrue(Version(1, 0, 0) < Version(2, 0, 0))
        self.assertTrue(Version(1, 0, 0) < Version(1, 1, 0))
        self.assertTrue(Version(1, 0, 0) < Version(1, 0, 1))
        self.assertFalse(Version(1, 0, 0) < Version(1, 0, 0))
        self.assertFalse(Version(2, 0, 0) < Version(1, 0, 0))
        self.assertFalse(Version(1, 2, 0) < Version(1, 1, 0))
        self.assertFalse(Version(1, 1, 2) < Version(1, 1, 1))
        self.assertTrue(Version(0, 1, 0) < Version(1, 0, 0))
        self.assertTrue(Version.from_string("1.0.0-alpha") < Version.from_string("1.0.0"))
        self.assertFalse(Version.from_string("1.0.0") < Version.from_string("1.0.0-alpha"))
        self.assertTrue(Version.from_string("1.0.0-alpha") < Version.from_string("1.0.0-beta"))
        self.assertFalse(Version.from_string("1.0.0-beta") < Version.from_string("1.0.0-alpha"))
        self.assertTrue(Version.from_string("1.0.0-rc") < Version.from_string("1.0.0-rc.3"))
        self.assertFalse(Version.from_string("1.0.0-rc.3") < Version.from_string("1.0.0-rc"))
        self.assertTrue(Version.from_string("1.0.0-rc.2") < Version.from_string("1.0.0-rc.3"))
        self.assertFalse(Version.from_string("1.0.0-rc.3") < Version.from_string("1.0.0-rc.2"))
        self.assertTrue(Version.from_string("0.2.2") < Version.from_string("0.2.3-rc"))

    def test_from_string(self):
        self.assertEqual(Version.from_string("1.5.7"), Version(1, 5, 7))
        self.assertEqual(Version.from_string("0.23.0"), Version(0, 23, 0))
        self.assertEqual(Version.from_string("0.0.0"), Version())
        self.assertEqual(Version.from_string("macOS_1.4.6", strip_scope="macOS"), Version(1, 4, 6))

        with self.assertRaises(ValueError):
            Version.from_string("macOS_1.4.6", strip_scope="something"), Version(1, 4, 6)
        with self.assertRaises(ValueError):
            Version.from_string("macOS_1.4.6"), Version(1, 4, 6)

        self.assertEqual(Version.from_string("1.5.9-rc"), Version(1, 5, 9, PreRelease("rc", 0)))
        self.assertEqual(Version.from_string("1.5.9-rc.0"), Version(1, 5, 9, PreRelease("rc", 0)))
        self.assertEqual(Version.from_string("1.5.9-alpha.34"), Version(1, 5, 9, PreRelease("alpha", 34)))

    def test_from_string_unknown_scope(self):
        with self.assertRaises(changes.UnknownScope):
            Version.from_string("1.3.4", strip_scope="macOS")

    def test_sort(self):
        input = [
            "1.2.3",
            "0.0.0",
            "12.0.6",
            "0.1.0",
            "0.0.0",
        ]
        output = [
            "0.0.0",
            "0.0.0",
            "0.1.0",
            "1.2.3",
            "12.0.6",
        ]
        input_versions = [Version.from_string(string) for string in input]
        self.assertNotEqual([str(version) for version in input_versions], output)
        self.assertEqual([str(version) for version in sorted(input_versions)], output)

    def test_initial_development(self):
        self.assertTrue(Version().initial_development)
        self.assertTrue(Version(0, 1, 4).initial_development)
        self.assertTrue(Version(0, 0, 1).initial_development)
        self.assertTrue(Version(0, 20, 0).initial_development)
        self.assertFalse(Version(1, 0, 0).initial_development)
        self.assertFalse(Version(200, 1, 0).initial_development)
        self.assertFalse(Version(2, 0, 10).initial_development)

    def test_is_pre_release(self):
        self.assertFalse(Version().is_pre_release)
        self.assertFalse(Version(0, 1, 4).is_pre_release)
        self.assertFalse(Version(0, 0, 1).is_pre_release)
        self.assertFalse(Version(0, 20, 0).is_pre_release)
        self.assertFalse(Version(1, 0, 0).is_pre_release)
        self.assertFalse(Version(200, 1, 0).is_pre_release)
        self.assertFalse(Version(2, 0, 10).is_pre_release)
        self.assertTrue(Version(1, 0, 0, PreRelease("rc")).is_pre_release)
        self.assertTrue(Version(1, 0, 0, PreRelease("rc", 0)).is_pre_release)
        self.assertTrue(Version(1, 0, 0, PreRelease("rc", 3)).is_pre_release)

    def test_increment(self):
        version = Version(1, 0, 0)
        version.bump_major()
        self.assertEqual(str(version), "2.0.0")
        version.bump_major()
        self.assertEqual(str(version), "2.0.0")

        version = Version(1, 0, 0)
        version.bump_minor()
        self.assertEqual(str(version), "1.1.0")
        version.bump_minor()
        self.assertEqual(str(version), "1.1.0")

        version = Version(1, 0, 0)
        version.bump_patch()
        self.assertEqual(str(version), "1.0.1")
        version.bump_patch()
        self.assertEqual(str(version), "1.0.1")

        version = Version(1, 0, 0)
        version.bump_minor()
        self.assertEqual(str(version), "1.1.0")
        version.bump_major()
        self.assertEqual(str(version), "2.0.0")
        version.bump_minor()
        self.assertEqual(str(version), "2.0.0")

        version = Version(1, 0, 0)
        version.bump_patch()
        self.assertEqual(str(version), "1.0.1")
        version.bump_major()
        self.assertEqual(str(version), "2.0.0")
        version.bump_patch()
        self.assertEqual(str(version), "2.0.0")

        with self.assertRaises(AssertionError):
            Version(2, 1, 0, PreRelease("alpha", 0)).bump_major()
        with self.assertRaises(AssertionError):
            Version(2, 1, 0, PreRelease("alpha", 0)).bump_minor()
        with self.assertRaises(AssertionError):
            Version(2, 1, 0, PreRelease("alpha", 0)).bump_patch()


        # TODO: Double check the behaviour of versions which are allowed to be pre-release but don't include changes.

        # TODO: Test that versions that are marked as 'pre-release' do not render pre-release components without changes
        #       and do render pre-release components with a change.
        # version = Version(4, 5, 0) + PreRelease("rc", 0)



if __name__ == '__main__':
    unittest.main()
