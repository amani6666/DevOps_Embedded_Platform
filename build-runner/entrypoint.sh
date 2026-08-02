#!/bin/bash
set -euo pipefail

# -------------------------------------------------------------------
# Zephyr Build Runner – Production Entrypoint
# -------------------------------------------------------------------

export ZEPHYR_BASE="${ZEPHYR_BASE:-/workspace/zephyrproject/zephyr}"

if [ -f "${ZEPHYR_BASE}/zephyr-env.sh" ]; then
    # shellcheck source=/dev/null
    source "${ZEPHYR_BASE}/zephyr-env.sh"
fi

# 1. Immediate pass-through for direct 'west' subcommands (e.g. west --version)
if [ "${1:-}" = "west" ]; then
    shift
    exec west "$@"
fi

# 2. Build execution banner & logs
echo "=== Zephyr Build Runner ==="
echo "ZEPHYR_BASE : ${ZEPHYR_BASE}"
echo "Working dir : $(pwd)"
echo "Args        : $*"

# Default values
BOARD="${BOARD:-esp32_devkitc_wroom/esp32/procpu}"
APP_DIR="${APP_DIR:-/app}"

# Strip leading "build" subcommand if passed explicitly
if [ "${1:-}" = "build" ]; then
    shift
fi

# Parse explicit flags
while [ $# -gt 0 ]; do
    case "$1" in
        -b|--board)
            if [ $# -lt 2 ]; then
                echo "ERROR: Missing argument for $1 option."
                exit 1
            fi
            BOARD="$2"
            shift 2
            ;;
        -d|--app-dir)
            if [ $# -lt 2 ]; then
                echo "ERROR: Missing argument for $1 option."
                exit 1
            fi
            APP_DIR="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

BUILD_DIR="${BUILD_DIR:-${APP_DIR}/build}"

echo "Board       : ${BOARD}"
echo "App dir     : ${APP_DIR}"
echo "Build dir   : ${BUILD_DIR}"

if [ ! -d "${APP_DIR}" ]; then
    echo "ERROR: Application directory '${APP_DIR}' does not exist."
    exit 1
fi

# Run the west build
echo ">>> Starting west build..."
west build \
    -p auto \
    -b "${BOARD}" \
    -d "${BUILD_DIR}" \
    "${APP_DIR}" \
    "$@"

# -------------------------------------------------------------------
# Post-build: expose binary location clearly for Agent 4 / CI
# -------------------------------------------------------------------
BIN_PATH="${BUILD_DIR}/zephyr/zephyr.bin"
ELF_PATH="${BUILD_DIR}/zephyr/zephyr.elf"

if [ -f "${BIN_PATH}" ]; then
    echo "=== BUILD SUCCESS ==="
    echo "Binary : ${BIN_PATH}"
    echo "ELF    : ${ELF_PATH}"
    ls -lh "${BIN_PATH}" "${ELF_PATH}" 2>/dev/null || true
    exit 0
else
    echo "=== BUILD FAILED ==="
    echo "Binary not found at ${BIN_PATH}"
    exit 1
fi