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

mapfile -t PROTOCOLS < <(bashio::config 'protocols[]')
mapfile -t WHITELIST < <(bashio::config 'whitelist[]')

# Log configuration
bashio::log.info "MQTT Host: ${MQTT_HOST}"
bashio::log.info "MQTT Port: ${MQTT_PORT}"
bashio::log.info "MQTT Topic: ${MQTT_TOPIC}"
bashio::log.info "Units: ${UNITS}"
bashio::log.info "Protocols: ${PROTOCOLS[*]:-All}"
bashio::log.info "Whitelist: ${WHITELIST[*]:-None}"

# Export for Python
export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export MQTT_TOPIC
export UNITS

export PROTOCOLS="$(IFS=,; echo "${PROTOCOLS[*]}")"
export WHITELIST="$(IFS=,; echo "${WHITELIST[*]}")"

# Build rtl_433 arguments
RTL_ARGS=(-F json)

for protocol in "${PROTOCOLS[@]}"; do
    [[ -n "$protocol" ]] && RTL_ARGS+=(-R "$protocol")
done

if [[ "$UNITS" == "si" ]]; then
    RTL_ARGS+=(-C si)
fi

bashio::log.info "Starting rtl_433..."
bashio::log.info "Arguments: ${RTL_ARGS[*]}"

# Pipe rtl_433 JSON directly into the Python bridge
exec rtl_433 "${RTL_ARGS[@]}" | python3 /app/bridge/main.py
