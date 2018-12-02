#!/bin/bash -e
#
# Assumes that the allwpilib repo is checked out to the correct branch
# that needs to be added to this repo
#
# This script is only intended to be used by maintainers of this
# repository, users should not need to use it.
#

abspath() {
  # $1 : relative filename
  echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

if [ "$1" == "" ]; then
    echo "Usage: $0 /path/to/allwpilib"
    exit 1
fi

ALLWPILIB=$(abspath "$1")
CSCORE_SRC=$(abspath "$(dirname "$0")/../cscore_src")

cd "$ALLWPILIB"

ORIG_BRANCH="$(git symbolic-ref HEAD 2>/dev/null)"

git checkout -b CSCORE_TMP

# TODO: this takes awhile
git filter-branch -f --index-filter 'git rm --cached -qr --ignore-unmatch -- . && git reset -q $GIT_COMMIT -- cscore wpiutil' --prune-empty

cd "$CSCORE_SRC"

git pull "$ALLWPILIB" CSCORE_TMP 

cd "$ALLWPILIB"

git checkout $ORIG_BRANCH
git branch -D CSCORE_TMP
