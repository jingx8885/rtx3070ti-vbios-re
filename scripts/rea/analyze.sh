#!/usr/bin/env bash
# REA analysis of the RTX 3070 Ti VBIOS real-mode entry segment.
set -uxo pipefail
OUT=/mnt/e/rea-nvidia-bios/out
mkdir -p "$OUT"
export PATH=/opt/rea-tools/node-v22.23.4-linux-x64/bin:$PATH
export GHIDRA_INSTALL_DIR=/opt/rea-tools/ghidra_12.1.4_PUBLIC
JAVAC=$(readlink -f "$(which javac)"); export JAVA_HOME=$(dirname "$(dirname "$JAVAC")")
export REA_ANALYSIS_PROVIDER=ghidra
TARGET=/mnt/e/rea-nvidia-bios/vbios_entry_msi.com

echo '=== doctor ==='
rea doctor --provider ghidra --json | tee "$OUT/doctor.json" | python3 -c "import sys,json;d=json.load(sys.stdin);print('healthy=',d['healthy'])" 2>/dev/null || rea doctor --provider ghidra --json | tee "$OUT/doctor.json"

echo '=== providers ==='
rea providers --json | tee "$OUT/providers.json"

echo '=== inspect (load-image admission) ==='
rea inspect "$TARGET" --target-format dos-com --provider ghidra --json | tee "$OUT/inspect.json"

echo '=== inspect-native-load-image ==='
rea inspect-native-load-image "$TARGET" --target-format dos-com --provider ghidra --json | tee "$OUT/loadimage.json"

echo '=== list procedures ==='
rea search "$TARGET" '' --kind procedures --target-format dos-com --provider ghidra --json | tee "$OUT/procedures.json"

echo '=== instructions at entry ==='
rea instructions "$TARGET" 0x10100 --target-format dos-com --provider ghidra --json | tee "$OUT/instr_entry.json"

echo '=== decompile entry ==='
rea decompile "$TARGET" 0x10100 --target-format dos-com --provider ghidra --json | tee "$OUT/decompile_entry.json"

echo DONE
