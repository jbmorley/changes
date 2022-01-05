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

from changes import Version


class VersionTestCase(unittest.TestCase):

    def test_str(self):
        self.assertEqual(str(Version()), "0.0.0")
        self.assertEqual(str(Version(0, 1, 1)), "0.1.1")
        self.assertEqual(str(Version(2, 10, 5)), "2.10.5")

    def test_comparators(self):

        # Equals.
        self.assertEqual(Version(), Version())
        self.assertEqual(Version(1, 10, 5), Version(1, 10, 5))
        self.assertNotEqual(Version(1, 10, 5), Version(2, 10, 5))
        self.assertNotEqual(Version(1, 10, 5), Version(1, 11, 5))
        self.assertNotEqual(Version(1, 10, 5), Version(1, 10, 10))

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

    def test_from_string(self):
        self.assertEqual(Version.from_string("1.5.7"), Version(1, 5, 7))
        self.assertEqual(Version.from_string("0.23.0"), Version(0, 23, 0))
        self.assertEqual(Version.from_string("0.0.0"), Version())
        self.assertEqual(Version.from_string("macOS_1.4.6", strip_scope="macOS"), Version(1, 4, 6))
        with self.assertRaises(ValueError):
            Version.from_string("macOS_1.4.6", strip_scope="something"), Version(1, 4, 6)
        with self.assertRaises(ValueError):
            Version.from_string("macOS_1.4.6"), Version(1, 4, 6)

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


if __name__ == '__main__':
    unittest.main()
