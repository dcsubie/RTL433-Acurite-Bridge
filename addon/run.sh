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

# Expand any accidental CSV blobs into individual integers.
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
WHITELIST=()
read_config_array 'protocols' PROTOCOLS
read_config_array 'whitelist' WHITELIST

NORMALIZED_PROTOCOLS=()
NORMALIZED_WHITELIST=()
normalize_int_list PROTOCOLS NORMALIZED_PROTOCOLS
normalize_int_list WHITELIST NORMALIZED_WHITELIST
PROTOCOLS=("${NORMALIZED_PROTOCOLS[@]}")
WHITELIST=("${NORMALIZED_WHITELIST[@]}")

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
    PROTOCOL_LABELS=()
    for protocol in "${PROTOCOLS[@]}"; do
        case "${protocol}" in
            10) PROTOCOL_LABELS+=("10=Acurite 896 rain") ;;
            11) PROTOCOL_LABELS+=("11=Acurite 609TXC") ;;
            40) PROTOCOL_LABELS+=("40=Acurite 5n1/3n1/Atlas/592TXR") ;;
            41) PROTOCOL_LABELS+=("41=Acurite 986 fridge") ;;
            55) PROTOCOL_LABELS+=("55=Acurite 606TX") ;;
            74) PROTOCOL_LABELS+=("74=Acurite 00275/00276") ;;
            163) PROTOCOL_LABELS+=("163=Acurite 590TX") ;;
            *) PROTOCOL_LABELS+=("${protocol}") ;;
        esac
    done
    bashio::log.info "Protocols: ${PROTOCOL_LABELS[*]}"
else
    bashio::log.info "Protocols: All (every rtl_433 decoder)"
fi
if ((${#WHITELIST[@]} > 0)); then
    bashio::log.info "Whitelist: ${WHITELIST[*]}"
else
    bashio::log.info "Whitelist: None (accept all decoded sensor IDs)"
fi

# Build rtl_433 arguments.
# 0.1.14 diagnostic: do not pass -R at all so EVERY decoder is enabled.
# This A/B-tests whether the protocols list / -R flags are why the 5n1
# disappeared. Morning's "-R 11,40,... -R 40 ..." still only registered
# 11+40+41+55+74 (rtl_433 prints a warning but still registers protocol 11).
RTL_ARGS=(-F json -M level)

if ((${#PROTOCOLS[@]} > 0)); then
    bashio::log.warning "0.1.14 diagnostic: ignoring configured protocols (${PROTOCOLS[*]}) and enabling ALL rtl_433 decoders"
    bashio::log.warning "Set protocols back after this test, or upgrade past 0.1.14 when normal -R filtering returns"
else
    bashio::log.info "Protocols list empty; enabling ALL rtl_433 decoders"
fi

if [[ "$UNITS" == "si" ]]; then
    RTL_ARGS+=(-C si)
fi

# Export for Python. Use RTL433_* names to avoid colliding with any
# container/environment variables, and never clobber the bash arrays used above.
export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export MQTT_TOPIC
export UNITS
export ADDON_VERSION="$(bashio::addon.version)"
export ADDON_NAME="RTL433 Acurite Bridge"
export ADDON_SUPPORT_URL="https://github.com/dcsubie/RTL433-Acurite-Bridge"
export RTL433_WHITELIST="$(IFS=,; echo "${WHITELIST[*]}")"

bashio::log.info "Bridge whitelist export: ${RTL433_WHITELIST:-None}"
bashio::log.info "Starting rtl_433..."
bashio::log.info "Arguments: ${RTL_ARGS[*]}"

# Keep the pipeline running even if one side warns/exits oddly.
# pipefail would tear down the whole add-on on rtl_433 non-zero exits.
set +o pipefail
rtl_433 "${RTL_ARGS[@]}" | python3 /app/bridge/main.py
pipeline_status=("${PIPESTATUS[@]}")
rtl_code=${pipeline_status[0]:-0}
python_code=${pipeline_status[1]:-0}
if [[ ${python_code} -ne 0 ]]; then
    bashio::exit.nok "Python bridge exited with code ${python_code}"
fi
if [[ ${rtl_code} -ne 0 ]]; then
    bashio::exit.nok "rtl_433 exited with code ${rtl_code}"
fi
bashio::exit.ok
