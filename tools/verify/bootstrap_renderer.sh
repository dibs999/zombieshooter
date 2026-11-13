#!/usr/bin/env bash
# Debian cloud image: verified Debian packages extracted as the ordinary user.
# No root, global APT configuration changes or TLS/signature bypasses.
set -euo pipefail
RUNTIME="${BUNKER_RUNTIME_DIR:-/workspace/.zombieshooter-runtime}"
APT_DIR="$RUNTIME/apt"
GRAPHICS_DIR="$RUNTIME/graphics"
mkdir -p "$APT_DIR/lists/partial" "$APT_DIR/cache/archives/partial" "$GRAPHICS_DIR"
test "$(dpkg --print-architecture)" = amd64
test -r /usr/share/keyrings/debian-archive-keyring.gpg
cat > "$APT_DIR/sources.list" <<EOF
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main
EOF
cat > "$APT_DIR/apt.conf" <<EOF
Dir::Etc::sourcelist "$APT_DIR/sources.list";
Dir::Etc::sourceparts "-";
Dir::Etc::parts "-";
Dir::State::lists "$APT_DIR/lists";
Dir::Cache "$APT_DIR/cache";
APT::Sandbox::User "$(id -un)";
EOF
export APT_CONFIG="$APT_DIR/apt.conf"
/usr/bin/apt-get update
cd "$GRAPHICS_DIR"
/usr/bin/apt-get download xvfb libxfont2 mesa-vulkan-drivers
for package in xvfb_*.deb libxfont2_*.deb mesa-vulkan-drivers_*.deb; do
    dpkg-deb -x "$package" root
done
echo "Software renderer extracted to $GRAPHICS_DIR/root"
