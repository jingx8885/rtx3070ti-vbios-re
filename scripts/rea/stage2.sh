#!/usr/bin/env bash
set -uxo pipefail
cd /opt/rea-tools
# wait for node tarball to finish (size stable + tar test)
for i in $(seq 1 60); do
  if tar tJf node.tar.xz >/dev/null 2>&1; then break; fi; sleep 5
done
tar xf node.tar.xz
export PATH=/opt/rea-tools/node-v22.23.4-linux-x64/bin:$PATH
node --version || exit 1
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openjdk-21-jdk-headless unzip xz-utils ca-certificates > /tmp/apt.log 2>&1
java -version 2>&1 | head -2
if [ ! -d ghidra_12.1.4_PUBLIC ]; then
  curl -fsSL -o ghidra.zip https://gh-proxy.com/https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip
  unzip -q ghidra.zip
fi
export GHIDRA_INSTALL_DIR=/opt/rea-tools/ghidra_12.1.4_PUBLIC
JAVAC=$(readlink -f "$(which javac)"); export JAVA_HOME=$(dirname "$(dirname "$JAVAC")")
npm install -g rea-agents > /tmp/npm.log 2>&1
rea --version || true
rea doctor --provider ghidra --json > /mnt/e/rea-nvidia-bios/doctor.json 2>&1 || true
echo STAGE2_DONE
