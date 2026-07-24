# RTL433 Acurite Bridge

RTL433 Acurite Bridge receives weather-station readings with an RTL-SDR receiver and publishes them to MQTT. Home Assistant discovers the supported measurements automatically.

## Requirements

- An RTL-SDR receiver connected to the Home Assistant host.
- A running MQTT broker, such as the Mosquitto Broker add-on.

## Setup

1. Install and start an MQTT broker.
2. Set **MQTT broker host** to the hostname or IP address of that broker. `core-mosquitto` is the usual hostname for the Mosquitto Broker add-on.
3. Enter MQTT credentials when your broker requires them.
4. Start this add-on and wait for your weather station to transmit.
5. Home Assistant creates a device for each detected weather station and adds its discovered entities automatically.

## Configuration

| Option | Description |
| --- | --- |
| MQTT broker host | Hostname or IP address of the MQTT broker. |
| MQTT broker port | MQTT broker port; normally `1883`. |
| MQTT username / password | Credentials for brokers that require authentication. |
| MQTT topic root | Prefix used for state topics. Each sensor publishes to `<topic root>/<sensor id>`. |
| Sensor whitelist | Optional list of sensor IDs to publish. Leave empty to accept every detected sensor. |
| RTL433 protocols | Decoder protocol numbers enabled in `rtl_433`. Restricting this list can reduce noise and unnecessary decoding. |
| Units | Use `si` for metric output. |

## Troubleshooting

- `bitbuffer_add_bit` warnings are usually radio noise or signals from unsupported devices. Restrict the enabled protocols to the one used by your station to reduce them.
- A tuner message such as `PLL not locked` during startup is not necessarily fatal. If sensor readings are received, the receiver is functioning.
- If no entities appear, confirm the MQTT connection in the add-on log and verify that the station is transmitting within receiver range.
