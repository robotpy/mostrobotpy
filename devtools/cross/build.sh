#!/bin/bash
# Shared by CI and the local Docker launcher. Run from the repository root.
set -euo pipefail
export PATH="/build/venv/cross/bin:/build/venv/build/bin:$PATH"
stage=${1:?Expected other, meson, or all}
shift
case "$stage" in
    other)
        /build/venv/bin/cross-python -m devtools ci build-other-wheels --no-test
        ;;
    meson)
        /build/venv/bin/cross-python -m devtools ci build-meson-wheels --no-test --cross=cross.txt "$@"
        ;;
    all)
        bash devtools/cross/build.sh other
        mkdir -p dist-other
        mv dist/*.whl dist-other/
        /build/venv/bin/cross-python -m devtools ci build-pure-wheels
        bash devtools/cross/build.sh meson "$@"
        ;;
    *) echo "Unknown build stage: $stage" >&2; exit 2 ;;
esac
