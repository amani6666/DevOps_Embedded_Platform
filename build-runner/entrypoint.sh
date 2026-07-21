#!/bin/bash
set -e

echo "=== Zephyr Build Runner ==="
echo "ZEPHYR_BASE: $ZEPHYR_BASE"
echo "Target board: ${BOARD:-esp32_devkitc_wroom/esp32/procpu}"

# Allow mounting project at /workspace/app or current dir
if [ -d "/workspace/app" ]; then
    cd /workspace/app
else
    mkdir -p /workspace/app
    cd /workspace/app
fi

exec west "$@"