#!/bin/bash
set -e

export ZEPHYR_BASE=/workspace/zephyrproject/zephyr

if [ -f "/workspace/zephyrproject/zephyr/zephyr-env.sh" ]; then
    source /workspace/zephyrproject/zephyr/zephyr-env.sh
fi

echo "=== Zephyr Build Runner ==="
echo "ZEPHYR_BASE: $ZEPHYR_BASE"

# Execute west build targeting /app
if [ $# -gt 0 ]; then
    exec west build -p auto -b esp32_devkitc_wroom /app
else
    exec west bui
fi