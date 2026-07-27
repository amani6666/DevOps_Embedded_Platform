#!/bin/bash
set -e

export ZEPHYR_BASE=/workspace/zephyrproject/zephyr

if [ -f "/workspace/zephyrproject/zephyr/zephyr-env.sh" ]; then
    source /workspace/zephyrproject/zephyr/zephyr-env.sh
fi

echo "=== Zephyr Build Runner ==="
echo "ZEPHYR_BASE: $ZEPHYR_BASE"

# Se placer dans le workspace Zephyr pour que 'west' reconnaisse toutes ses commandes
cd /workspace/zephyrproject

# Executer west build en lui indiquant le dossier source de votre application montée
exec west "$@"