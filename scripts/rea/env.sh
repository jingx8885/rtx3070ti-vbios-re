#!/usr/bin/env bash
export PATH=/opt/rea-tools/node-v22.23.4-linux-x64/bin:$PATH
export GHIDRA_INSTALL_DIR=/opt/rea-tools/ghidra_12.1.4_PUBLIC
JAVAC=$(readlink -f "$(which javac)")
export JAVA_HOME=$(dirname "$(dirname "$JAVAC")")
export REA_ANALYSIS_PROVIDER=ghidra
exec "$@"
