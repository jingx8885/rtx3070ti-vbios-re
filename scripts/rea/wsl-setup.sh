#!/usr/bin/env bash
set -euxo pipefail
mkdir -p /opt/rea-tools /mnt/e/rea-nvidia-bios
cd /opt/rea-tools
export PATH=/opt/rea-tools/node-v22.23.4-linux-x64/bin:$PATH
if [ ! -x node-v22.23.4-linux-x64/bin/node ]; then
  curl -fsSL -o node.tar.xz https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.xz
  tar xf node.tar.xz
fi
node --version
npm --version
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-21-jdk-headless unzip xz-utils ca-certificates
java -version 2>&1 | head -3
if [ ! -d ghidra_12.1.4_PUBLIC ]; then
  curl -fSL -o ghidra.zip https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip
  unzip -q ghidra.zip
fi
export GHIDRA_INSTALL_DIR=/opt/rea-tools/ghidra_12.1.4_PUBLIC
JAVAC=$(readlink -f "$(which javac)")
export JAVA_HOME=$(dirname "$(dirname "$JAVAC")")
echo "JAVA_HOME=$JAVA_HOME"
npm install -g rea-agents
rea --version || true
echo '=== DOCTOR ==='
rea doctor --provider ghidra --json | tee /mnt/e/rea-nvidia-bios/doctor.json
echo '=== SETUP DONE ==='
