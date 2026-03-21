# HDR Notify for Kodi

A Kodi service addon that detects the HDR/SDR state of the currently playing video and sends it to external services -- so they can react automatically without relying on signal auto-detection.

## The Problem

[HyperHDR](https://github.com/awawa-dev/HyperHDR) provides ambient lighting with HDR tone mapping support, but it needs to know *when* to apply tone mapping. Automatic detection is unreliable on some setups, causing washed-out colors or incorrect tone mapping. Similarly, you may want [Home Assistant](https://www.home-assistant.io/) to react to HDR content -- for example, adjusting room lighting or triggering scenes.

## How It Works

```
Kodi (playing video)
  |
  |  onAVStarted / onPlayBackStopped / onPlayBackEnded
  |
  v
HDR Notify (this addon)
  |
  |  reads VideoPlayer.HdrType
  |
  |--- HyperHDR:        POST /json-rpc  {"command":"videomodehdr", "HDR": 1|0}
  |
  '--- Home Assistant:  POST /api/webhook/<id>  {"hdr": true|false, "hdr_type": "..."}
```

1. When video playback starts, the addon reads the [`VideoPlayer.HdrType`](https://kodi.wiki/view/InfoLabels) InfoLabel
2. Any non-empty value (e.g. `hdr10`, `dolbyvision`, `hlg`) means HDR is active
3. The addon sends the state to whichever targets are enabled
4. When playback stops or ends, it sends SDR (reset) to all enabled targets

Both targets are independent -- you can enable one, both, or neither.

## Compatibility

- **Kodi 20 (Nexus)** and later -- the `VideoPlayer.HdrType` InfoLabel was introduced in Kodi 20
- No external dependencies -- uses Python stdlib only

## Installation

1. Go to the [Releases](../../releases) page
2. Download the latest `service.video.hdrnotify-*.zip`
3. In Kodi: **Settings > Add-ons > Install from zip file** > select the downloaded ZIP
4. Configure the addon via **Settings > Add-ons > My add-ons > Services > HDR Notify**

## Configuration

The addon settings are split into two tabs:

### HyperHDR

| Setting | Default | Description |
|---------|---------|-------------|
| Enable HyperHDR | On | Toggle HyperHDR notifications |
| Host | `127.0.0.1` | HyperHDR IP or hostname |
| Port | `8090` | JSON API port (default HTTPS port: `8443`) |
| Use HTTPS | Off | Connect via HTTPS |
| API Token | *(empty)* | Auth token, if [token-based authentication](https://github.com/awawa-dev/HyperHDR/wiki) is enabled |

The addon sends the [`videomodehdr`](https://github.com/awawa-dev/HyperHDR) command to the HyperHDR JSON API at `/json-rpc`.

### Home Assistant

| Setting | Default | Description |
|---------|---------|-------------|
| Enable Home Assistant | Off | Toggle HA webhook notifications |
| Host | `127.0.0.1` | Home Assistant IP or hostname |
| Port | `8123` | HA port |
| Use HTTPS | Off | Connect via HTTPS |
| Webhook ID | *(empty)* | The webhook ID from your HA automation trigger |

The addon sends a JSON payload to the HA [webhook trigger](https://www.home-assistant.io/docs/automation/trigger/#webhook-trigger) endpoint:

```json
{"hdr": true, "hdr_type": "hdr10"}
```

No authentication token is needed -- HA webhooks are auth-free by design.

#### Example Home Assistant Automation

```yaml
automation:
  - alias: "React to Kodi HDR state"
    trigger:
      - platform: webhook
        webhook_id: "kodi_hdr_state"
        allowed_methods:
          - POST
        local_only: true
    action:
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.hdr }}"
            sequence:
              - service: light.turn_off
                target:
                  entity_id: light.living_room
        default:
          - service: light.turn_on
            target:
              entity_id: light.living_room
```

## Related Projects

- [HyperHDR](https://github.com/awawa-dev/HyperHDR) -- Open-source ambient lighting with HDR tone mapping
- [Home Assistant](https://www.home-assistant.io/) -- Open-source home automation platform
- [Kodi](https://kodi.tv/) -- Open-source media center
- [CoreELEC](https://coreelec.org/) -- Lightweight Kodi-focused OS for Amlogic devices

## License

[MIT](LICENSE.md)
