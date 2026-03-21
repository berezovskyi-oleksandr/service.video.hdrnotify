import json
import ssl
import urllib.request

import xbmc
import xbmcaddon

ADDON_ID = "service.video.hdrnotify"
LOG_PREFIX = "[HDR Notify]"


def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"{LOG_PREFIX} {msg}", level)


def read_settings():
    addon = xbmcaddon.Addon(ADDON_ID)
    return {
        "hyperhdr_enabled": addon.getSettingBool("hyperhdr_enabled"),
        "hyperhdr_host": addon.getSetting("hyperhdr_host"),
        "hyperhdr_port": addon.getSettingInt("hyperhdr_port"),
        "hyperhdr_ssl": addon.getSettingBool("hyperhdr_ssl"),
        "hyperhdr_token": addon.getSetting("hyperhdr_token"),
        "ha_enabled": addon.getSettingBool("ha_enabled"),
        "ha_host": addon.getSetting("ha_host"),
        "ha_port": addon.getSettingInt("ha_port"),
        "ha_ssl": addon.getSettingBool("ha_ssl"),
        "ha_webhook_id": addon.getSetting("ha_webhook_id"),
    }


def _post_json(url, data, use_ssl=False):
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    ctx = None
    if use_ssl:
        ctx = ssl.create_default_context()
    urllib.request.urlopen(req, timeout=2, context=ctx)


def notify_hyperhdr(settings, is_hdr):
    host = settings["hyperhdr_host"]
    port = settings["hyperhdr_port"]
    if not host:
        return
    scheme = "https" if settings["hyperhdr_ssl"] else "http"
    url = f"{scheme}://{host}:{port}/json-rpc"
    use_ssl = settings["hyperhdr_ssl"]
    try:
        token = settings["hyperhdr_token"]
        if token:
            _post_json(
                url,
                {"command": "authorize", "subcommand": "login", "token": token},
                use_ssl,
            )
        _post_json(
            url,
            {"command": "videomodehdr", "tan": 1, "HDR": 1 if is_hdr else 0},
            use_ssl,
        )
        log(f"HyperHDR notified: HDR={'on' if is_hdr else 'off'}")
    except Exception as e:
        log(f"HyperHDR error: {e}", xbmc.LOGWARNING)


def notify_homeassistant(settings, is_hdr, hdr_type):
    host = settings["ha_host"]
    webhook_id = settings["ha_webhook_id"]
    if not host or not webhook_id:
        return
    port = settings["ha_port"]
    scheme = "https" if settings["ha_ssl"] else "http"
    url = f"{scheme}://{host}:{port}/api/webhook/{webhook_id}"
    try:
        _post_json(
            url,
            {"hdr": is_hdr, "hdr_type": hdr_type},
            settings["ha_ssl"],
        )
        log(f"Home Assistant notified: hdr={is_hdr}, hdr_type='{hdr_type}'")
    except Exception as e:
        log(f"Home Assistant error: {e}", xbmc.LOGWARNING)


def notify_targets(settings, is_hdr, hdr_type=""):
    if settings["hyperhdr_enabled"]:
        notify_hyperhdr(settings, is_hdr)
    if settings["ha_enabled"]:
        notify_homeassistant(settings, is_hdr, hdr_type)


class HDRMonitor(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.settings = read_settings()

    def onSettingsChanged(self):
        self.settings = read_settings()
        log("Settings reloaded")


class HDRPlayer(xbmc.Player):
    def __init__(self, monitor):
        super().__init__()
        self._monitor = monitor

    def onAVStarted(self):
        hdr_type = xbmc.getInfoLabel("VideoPlayer.HdrType")
        is_hdr = bool(hdr_type)
        log(f"Playback started: hdr_type='{hdr_type}', is_hdr={is_hdr}")
        notify_targets(self._monitor.settings, is_hdr, hdr_type)

    def onPlayBackStopped(self):
        log("Playback stopped")
        notify_targets(self._monitor.settings, False)

    def onPlayBackEnded(self):
        log("Playback ended")
        notify_targets(self._monitor.settings, False)


if __name__ == "__main__":
    log("Service started")
    monitor = HDRMonitor()
    player = HDRPlayer(monitor)

    while not monitor.abortRequested():
        if monitor.waitForAbort(1):
            break

    log("Service stopped")
