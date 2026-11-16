#!/usr/bin/env bash
# Debian cloud image: verified Debian packages extracted as the ordinary user.
# No root, global APT configuration changes or TLS/signature bypasses.
set -euo pipefail
RUNTIME="${BUNKER_RUNTIME_DIR:-/workspace/.zombieshooter-runtime}"
APT_DIR="$RUNTIME/apt"
GRAPHICS_DIR="$RUNTIME/graphics"
mkdir -p "$APT_DIR/lists/partial" "$APT_DIR/cache/archives/partial" "$APT_DIR/empty" "$GRAPHICS_DIR"
test "$(dpkg --print-architecture)" = amd64
test -r /usr/share/keyrings/debian-archive-keyring.gpg
CODENAME="bookworm"
if [ -r /etc/os-release ]; then
    CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-bookworm}")"
fi
: > "$APT_DIR/status"
cat > "$APT_DIR/sources.list" <<EOF
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian $CODENAME main
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian $CODENAME-updates main
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian-security $CODENAME-security main
EOF
cat > "$APT_DIR/apt.conf" <<EOF
Dir::Etc::sourcelist "$APT_DIR/sources.list";
Dir::Etc::sourceparts "$APT_DIR/empty";
Dir::Etc::parts "$APT_DIR/empty";
Dir::State::lists "$APT_DIR/lists";
Dir::State::status "$APT_DIR/status";
Dir::Cache "$APT_DIR/cache";
Dir::Cache::archives "$APT_DIR/cache/archives";
APT::Sandbox::User "$(id -un)";
EOF
export APT_CONFIG="$APT_DIR/apt.conf"
/usr/bin/apt-get update
cd "$GRAPHICS_DIR"
rm -f ./*.deb
/usr/bin/apt-get download xvfb libxfont2 mesa-vulkan-drivers
for package in xvfb_*.deb libxfont2_*.deb mesa-vulkan-drivers_*.deb; do
    dpkg-deb -x "$package" root
done
icd_dir="$GRAPHICS_DIR/root/usr/share/vulkan/icd.d"
for icd in "$icd_dir"/lvp_icd*.json; do
    if [ -f "$icd" ]; then
        sed -i 's|"/usr/lib/x86_64-linux-gnu/libvulkan_lvp.so"|"libvulkan_lvp.so"|g' "$icd"
    fi
done
if [ -f "$icd_dir/lvp_icd.x86_64.json" ] && [ ! -e "$icd_dir/lvp_icd.json" ]; then
    cp "$icd_dir/lvp_icd.x86_64.json" "$icd_dir/lvp_icd.json"
fi
echo "Software renderer extracted to $GRAPHICS_DIR/root"
