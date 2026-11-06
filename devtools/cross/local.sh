#!/bin/bash
set -euo pipefail
mkdir /work
cp -a /source/. /work/
cd /work
export PATH="/build/venv/cross/bin:/build/venv/build/bin:$PATH"
export CCACHE_DIR=/cache/ccache
export CCACHE_BASEDIR=/work
export HATCH_ROBOTPY_CACHE=/cache/downloads
export PIP_CACHE_DIR=/cache/pip
trap 'ccache --show-stats' EXIT
if ! command -v ccache >/dev/null; then
    apt-get update
    apt-get install -y --no-install-recommends ccache
fi
bash devtools/cross/setup.sh
/build/venv/bin/build-pip --disable-pip-version-check install -r rdev_requirements.txt
bash devtools/cross/build.sh all "$@"
cp dist/*.whl dist-other/*.whl /export/
chown "${EXPORT_UID}:${EXPORT_GID}" /export/*.whl
