#!/usr/bin/with-contenv bashio

set -e

bashio::log.info "========================================="
bashio::log.info "RTL433 Acurite Bridge"
bashio::log.info "Version: ${HOSTNAME:-Development}"
bashio::log.info "========================================="

MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_TOPIC=$(bashio::config 'mqtt_topic')
UNITS=$(bashio::config 'units')

bashio::log.info "MQTT Host: ${MQTT_HOST}"
bashio::log.info "MQTT Port: ${MQTT_PORT}"
bashio::log.info "MQTT Topic: ${MQTT_TOPIC}"
bashio::log.info "Units: ${UNITS}"

RTL_ARGS="-F json"

# Configure protocols
for protocol in $(bashio::config 'protocols | join(" ")'); do
    RTL_ARGS="${RTL_ARGS} -R ${protocol}"
done

# Configure whitelist
for id in $(bashio::config 'whitelist | join(" ")'); do
    RTL_ARGS="${RTL_ARGS} -K ${id}"
done

if [ "${UNITS}" = "si" ]; then
    RTL_ARGS="${RTL_ARGS} -C si"
fi

bashio::log.info "Starting rtl_433..."
bashio::log.info "Arguments: ${RTL_ARGS}"

# Start rtl_433 in the background
rtl_433 ${RTL_ARGS} >/tmp/rtl433.json &
RTL_PID=$!

bashio::log.info "Starting MQTT bridge..."

python3 /app/main.py

wait ${RTL_PID}
