#!/usr/bin/env bash
#
# Local development harness for the RTL433 Acurite Bridge.
#
# Replays recorded rtl_433 JSON (dev/sample_rtl433.jsonl by default) into the
# Python bridge, pointed at a local MQTT broker. This mirrors what run.sh does
# in production (`rtl_433 -F json | python3 /app/bridge/main.py`) but without
# requiring RTL-SDR hardware.
#
# Usage:
#   dev/run_bridge.sh [path-to-jsonl]
#
# Assumes a broker is reachable at MQTT_HOST:MQTT_PORT (defaults to the local
# dev broker started via .cursor/mosquitto.conf).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLE_FILE="${1:-${REPO_ROOT}/dev/sample_rtl433.jsonl}"
PYTHON_BIN="${PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python3}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
    PYTHON_BIN="python3"
fi

export MQTT_HOST="${MQTT_HOST:-127.0.0.1}"
export MQTT_PORT="${MQTT_PORT:-1883}"
export MQTT_USERNAME="${MQTT_USERNAME:-}"
export MQTT_PASSWORD="${MQTT_PASSWORD:-}"
export MQTT_TOPIC="${MQTT_TOPIC:-rtl_433}"
export UNITS="${UNITS:-si}"
export WHITELIST="${WHITELIST:-}"
export ADDON_VERSION="${ADDON_VERSION:-0.1.6}"
export ADDON_NAME="${ADDON_NAME:-RTL433 Acurite Bridge}"
export ADDON_SUPPORT_URL="${ADDON_SUPPORT_URL:-https://github.com/dcsubie/RTL433-Acurite-Bridge}"

echo "Replaying ${SAMPLE_FILE} into the bridge (broker ${MQTT_HOST}:${MQTT_PORT})" >&2

# Feed each line with a short delay so the paho network loop flushes publishes.
{
    while IFS= read -r line; do
        printf '%s\n' "${line}"
        sleep 0.5
    done < "${SAMPLE_FILE}"
    sleep 1
} | "${PYTHON_BIN}" "${REPO_ROOT}/addon/bridge/main.py"
