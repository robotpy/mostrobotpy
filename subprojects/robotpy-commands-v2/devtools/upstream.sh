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

cd $(dirname "$0")/..

if [ ! -z "$(git status --porcelain --untracked-files=no)" ]; then 
    echo "Working tree is dirty, exiting"
    exit 1
fi

ORIG_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null)"


pushd "$ALLWPILIB"

# TODO: this takes awhile
git subtree split --prefix=wpilibNewCommands/src/main/native/ -b cmd-v2-upstream

popd


git checkout upstream

git subtree pull --prefix commands2/src $ALLWPILIB cmd-v2-upstream

git checkout $ORIG_BRANCH