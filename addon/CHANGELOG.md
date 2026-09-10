# Changelog

## 0.1.20

- Log every decoded packet at INFO with id, model, rssi/snr/noise/freq
- Log first-heard sensor IDs and each successful publish
- Log whitelist skips at INFO (no longer silent)
- Keep 0.1.19 RF defaults (gain 40, `-Y classic`, clean `-R` flags)

## 0.1.19

- Keep the morning 0.1.7/0.1.16 bridge runtime
- Build upstream-style `-R` flags (`-R 11 -R 40 ...`, no CSV blob warning)
- Add RF options: `frequency`, `gain` (default `40`), `ppm`
- Add `classic_demod` (default `true`) for rtl_433 `-Y classic`
- Allow empty whitelist/protocols in the HA config UI again

## 0.1.16

- Restore the morning **0.1.7** add-on runtime (bridge, discovery, `run.sh`)
  that successfully decoded sensor 784 / 5n1 before later updates
- Version bump only so Home Assistant can install the rollback over 0.1.14+

## 0.1.14

- Diagnostic build: ignore the `protocols` list and run rtl_433 with all
  decoders enabled (no `-R` filters), plus `-M level`
- Log every decoded packet id/model (not only the first per id)
- Note: morning's `-R 11,40,41,55,74 -R 40 ...` still registered the same
  protocol set as `-R 11 -R 40 ...` (rtl_433 warns on the CSV form but still
  enables protocol 11)

## 0.1.13

- Drain rtl_433 stdout while seeding retained MQTT state so startup cannot
  block the SDR pipe (weaker stations were the first to disappear)
- Ignore non-numeric retained topics like `rtl_433/status` without warnings

## 0.1.12

- Allow clearing/omitting `whitelist` and `protocols` in the HA config UI
  (schema uses optional list items so an empty list is valid)

## 0.1.11

- Merge partial rtl_433 packets into last-known sensor state so Acurite 5n1
  alternating temp/wind/rain messages do not wipe retained MQTT fields
- Seed that merge cache from retained MQTT on startup (avoids wipe on restart)
- Log each newly heard sensor id/model and each published update
- Relax pipeline `pipefail` so rtl_433 warnings do not kill the add-on

## 0.1.10

- Fix sensor whitelist handoff to Python (`RTL433_WHITELIST`)
- Log the active whitelist and skipped non-whitelisted sensors
- Avoid `exec` on the left side of the rtl_433 | python pipeline

## 0.1.9

- Fix rtl_433 protocol flags so each `-R` gets one protocol number
  (`-R 11 -R 40 ...` instead of `-R 11,40,41,55,74`)

## 0.1.8

- Switch to MQTT device discovery with safe migration of legacy per-entity
  discovery topics

## 0.1.7

- Position the add-on as Acurite-first but usable by others
- Document default protocols and first-run whitelist flow
- Log human-readable protocol labels at startup

## 0.1.6

- Fix bashio parsing of `protocols` and `whitelist` arrays

## 0.1.5

- MQTT reconnect improvements

## 0.1.4

- Fix Home Assistant update detection / repository pin

## 0.1.3

- Version bump for Home Assistant updates

## 0.1.2

- MQTT modernization and documentation

## 0.1.1

- Initial public add-on packaging
