#!/usr/bin/with-contenv bashio
set -euo pipefail

bashio::log.info "========================================="
bashio::log.info "RTL433 Acurite Bridge"
bashio::log.info "========================================="

# Read configuration
MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USERNAME=$(bashio::config 'mqtt_username')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')
MQTT_TOPIC=$(bashio::config 'mqtt_topic')
UNITS=$(bashio::config 'units')

# Read list options by index. bashio::config 'key[]' is not valid and returns
# empty, which made logs show "All"/"None" even when values were configured.
read_config_array() {
    local key="$1"
    local -n __out_array="$2"
    local length value
    local i=0

    __out_array=()
    length="$(bashio::config "${key} | length")"
    if ! [[ "${length}" =~ ^[0-9]+$ ]]; then
        length=0
    fi

    for ((i = 0; i < length; i++)); do
        value="$(bashio::config "${key}[${i}]")"
        if [[ -n "${value}" && "${value}" != "null" ]]; then
            __out_array+=("${value}")
        fi
    done
}

# Expand accidental CSV blobs into individual integers.
# rtl_433's -R flag accepts exactly one protocol number per flag.
normalize_int_list() {
    local -n __source_array="$1"
    local -n __dest_array="$2"
    local entry part
    local -a parts=()
    local -A seen=()

    __dest_array=()
    for entry in "${__source_array[@]}"; do
        entry="${entry// /}"
        if [[ -z "${entry}" || "${entry}" == "null" ]]; then
            continue
        fi

        parts=()
        if [[ "${entry}" == *,* ]]; then
            IFS=',' read -r -a parts <<< "${entry}"
        else
            parts=("${entry}")
        fi

        for part in "${parts[@]}"; do
            part="${part// /}"
            if [[ "${part}" =~ ^[0-9]+$ ]]; then
                if [[ -z "${seen[$part]+x}" ]]; then
                    seen["${part}"]=1
                    __dest_array+=("${part}")
                fi
            else
                bashio::log.warning "Ignoring invalid protocol/whitelist entry: ${part}"
            fi
        done
    done
}

PROTOCOLS=()
read_config_array 'protocols' PROTOCOLS

NORMALIZED_PROTOCOLS=()
normalize_int_list PROTOCOLS NORMALIZED_PROTOCOLS
PROTOCOLS=("${NORMALIZED_PROTOCOLS[@]}")

# Whitelist is a plain string in the UI (e.g. "784" or "784,220").
WHITELIST_RAW="$(bashio::config 'whitelist')"
WHITELIST=()
if [[ -n "${WHITELIST_RAW}" && "${WHITELIST_RAW}" != "null" ]]; then
    # Allow commas and/or spaces: "784", "784,220", "784 220"
    WHITELIST_RAW="${WHITELIST_RAW//,/ }"
    # shellcheck disable=SC2206
    WHITELIST_CANDIDATES=(${WHITELIST_RAW})
    normalize_int_list WHITELIST_CANDIDATES WHITELIST
fi

# Prefer Supervisor MQTT service discovery when using the default broker
# host and no username was set in the add-on options. Explicit credentials
# or a custom broker host always win.
if [[ "${MQTT_HOST}" == "core-mosquitto" ]] \
    && [[ -z "${MQTT_USERNAME}" ]] \
    && bashio::services.available "mqtt"; then
    MQTT_HOST=$(bashio::services "mqtt" "host")
    MQTT_PORT=$(bashio::services "mqtt" "port")
    MQTT_USERNAME=$(bashio::services "mqtt" "username")
    MQTT_PASSWORD=$(bashio::services "mqtt" "password")
    bashio::log.info "Configured MQTT from Supervisor service discovery"
fi

# Log configuration (never log the password)
bashio::log.info "MQTT Host: ${MQTT_HOST}"
bashio::log.info "MQTT Port: ${MQTT_PORT}"
bashio::log.info "MQTT Topic: ${MQTT_TOPIC}"
bashio::log.info "Units: ${UNITS}"
if ((${#PROTOCOLS[@]} > 0)); then
    bashio::log.info "Protocols: ${PROTOCOLS[*]}"
else
    bashio::log.info "Protocols: All"
fi
if ((${#WHITELIST[@]} > 0)); then
    bashio::log.info "Whitelist: ${WHITELIST[*]}"
else
    bashio::log.info "Whitelist: None"
fi

# Export for Python
export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export MQTT_TOPIC
export UNITS
export ADDON_VERSION="$(bashio::addon.version)"
export ADDON_NAME="RTL433 Acurite Bridge"
export ADDON_SUPPORT_URL="https://github.com/dcsubie/RTL433-Acurite-Bridge"

# Build rtl_433 arguments BEFORE any CSV export. Assigning a CSV string back
# to PROTOCOLS only replaces index 0 and leaves 40,41,55,74 in place, which
# produced: -R 11,40,41,55,74 -R 40 -R 41 -R 55 -R 74
RTL_ARGS=(-F json)

for protocol in "${PROTOCOLS[@]}"; do
    RTL_ARGS+=(-R "${protocol}")
done

if [[ "$UNITS" == "si" ]]; then
    RTL_ARGS+=(-C si)
fi

export RTL433_WHITELIST="$(IFS=,; echo "${WHITELIST[*]}")"
export WHITELIST="${RTL433_WHITELIST}"

bashio::log.info "Starting rtl_433..."
bashio::log.info "Arguments: ${RTL_ARGS[*]}"

# Pipe rtl_433 JSON directly into the Python bridge
exec rtl_433 "${RTL_ARGS[@]}" | python3 /app/bridge/main.py
