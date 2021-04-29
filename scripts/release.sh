#!/bin/bash

changes release --push --command 'gh release create $CHANGES_TAG --title "$CHANGES_TITLE" --notes "$CHANGES_NOTES"' "$@"
