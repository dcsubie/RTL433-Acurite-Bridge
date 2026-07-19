#!/usr/bin/with-contenv bashio
set -euo pipefail

bashio::log.info "========================================="
bashio::log.info "RTL433 Acurite Bridge"
bashio::log.info "========================================="

MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_TOPIC=$(bashio::config 'mqtt_topic')
UNITS=$(bashio::config 'units')

bashio::log.info "MQTT Host: ${MQTT_HOST}"
bashio::log.info "MQTT Port: ${MQTT_PORT}"
bashio::log.info "MQTT Topic: ${MQTT_TOPIC}"
bashio::log.info "Units: ${UNITS}"

RTL_ARGS=(-F json)

mapfile -t PROTOCOLS < <(bashio::config 'protocols[]')
for protocol in "${PROTOCOLS[@]}"; do
    RTL_ARGS+=(-R "$protocol")
done

mapfile -t WHITELIST < <(bashio::config 'whitelist[]')
for id in "${WHITELIST[@]}"; do
    RTL_ARGS+=(-K "$id")
done

if [ "${UNITS}" = "si" ]; then
    RTL_ARGS+=(-C si)
fi

bashio::log.info "Starting rtl_433..."
bashio::log.info "Arguments: ${RTL_ARGS[*]}"

rtl_433 "${RTL_ARGS[@]}" -F json | python3 /app/bridge/main.py