#!/bin/bash
# Keep in sync with robotpy/build-actions/setup-cross-meson@v2027.
set -euo pipefail
cross_dir="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.local/share/meson/cross
toolchain_found=false
for entry in \
    arm-frc2025-linux-gnueabi:roborio \
    armv6-bookworm-linux-gnueabihf:bookworm \
    aarch64-bookworm-linux-gnu:systemcore_bookworm \
    aarch64-systemcore2027-linux-gnu:systemcore_2027; do
    if command -v "${entry%:*}-g++" >/dev/null; then
        cp "$cross_dir/${entry#*:}.txt" ~/.local/share/meson/cross/cross.txt
        toolchain_found=true
        break
    fi
done
if [[ $toolchain_found == false ]]; then
    echo 'No known cross toolchain found' >&2
    exit 1
fi
/build/venv/bin/cross-pip --disable-pip-version-check install meson
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cd "$scratch"
for package in ninja pkgconf; do
    /build/venv/bin/build-pip --disable-pip-version-check download --no-deps "$package"
    for wheel in "$package"-*.whl; do
        renamed=$(echo "$wheel" | sed -E 's/([^-]+-[^-]+-[^-]+)-.*/\1-none-any.whl/')
        mv "$wheel" "$renamed"
        /build/venv/bin/cross-pip --disable-pip-version-check install "$renamed"
        rm "$renamed"
    done
done
if [[ -n ${GITHUB_PATH:-} ]]; then
    echo /build/venv/cross/bin:/build/venv/build/bin >> "$GITHUB_PATH"
fi
