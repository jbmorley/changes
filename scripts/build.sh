#!/bin/bash

# Copyright (c) 2021-2024 Jason Morley
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

set -e
set -o pipefail
set -x
set -u

ROOT_DIRECTORY="$( cd "$( dirname "$( dirname "${BASH_SOURCE[0]}" )" )" &> /dev/null && pwd )"
BUILD_DIRECTORY="$ROOT_DIRECTORY/dist"

CHANGES_SCRIPT="$ROOT_DIRECTORY/changes"

# Configure the path.
PATH=$PATH:"$ROOT_DIRECTORY"

# Write outputs to /dev/null if we're not running under GitHub Actions.
GITHUB_OUTPUT="${GITHUB_OUTPUT:-/dev/null}"

# Clean up and recreate the output directories.
if [ -d "$BUILD_DIRECTORY" ] ; then
    rm -r "$BUILD_DIRECTORY"
fi
mkdir -p "$BUILD_DIRECTORY"

# Determine the version.
export VERSION=$($CHANGES_SCRIPT version)
export RELEASED_VERSION=$($CHANGES_SCRIPT version --released)

# Build the package.
pipenv run python -m build

# Check if the package needs a release and report it to GitHub Actions.
if [[ "$VERSION" == "$RELEASED_VERSION" ]]; then
    echo "needs_release=false" >> "$GITHUB_OUTPUT"
else
    echo "needs_release=true" >> "$GITHUB_OUTPUT"
fi
