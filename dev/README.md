# Local development

Tools for running and testing the RTL433 Acurite Bridge without RTL-SDR
hardware or a full Home Assistant install.

In production the add-on runs `rtl_433 -F json | python3 /app/bridge/main.py`
(see `addon/run.sh`). Locally we replace the SDR with recorded JSON and use a
local Mosquitto broker instead of the Supervisor-managed one.

## Prerequisites

Cloud Agents get these automatically from `.cursor/environment.json`. To set up
manually:

```bash
sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients rtl-433 python3-venv
python3 -m venv .venv
./.venv/bin/pip install -r addon/requirements.txt
```

## Run the bridge end-to-end

1. Start a local broker (the Cloud Agent env starts this automatically as the
   `mqtt-broker` terminal):

   ```bash
   mosquitto -c .cursor/mosquitto.conf
   ```

2. In another terminal, watch what the bridge publishes:

   ```bash
   mosquitto_sub -h 127.0.0.1 -p 1883 -v -t 'homeassistant/#' -t 'rtl_433/#'
   ```

3. Replay sample sensor data through the bridge:

   ```bash
   dev/run_bridge.sh
   ```

You should see Home Assistant MQTT Discovery configs on `homeassistant/...`,
retained sensor state on `rtl_433/<sensor_id>`, and bridge availability
(`online` / `offline`) on `rtl_433/bridge/status`.

## Using real hardware

With an RTL-SDR receiver plugged in, replace the replay with the real decoder:

```bash
rtl_433 -F json -C si | ./.venv/bin/python3 addon/bridge/main.py
```
