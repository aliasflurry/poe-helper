import json
import re
import threading
import urllib.error
import urllib.request
from typing import Callable, Dict, Optional, Tuple

from app_config import APP_VERSION, GITHUB_REPO


UpdateResult = Dict[str, object]


def _version_tuple(version: str) -> Tuple[int, ...]:
    parts = re.findall(r"\d+", version)
    return tuple(int(part) for part in parts) if parts else (0,)


def is_newer_version(latest_version: str, current_version: str = APP_VERSION) -> bool:
    latest = _version_tuple(latest_version)
    current = _version_tuple(current_version)
    max_len = max(len(latest), len(current))
    latest += (0,) * (max_len - len(latest))
    current += (0,) * (max_len - len(current))
    return latest > current


def _asset_download_url(release: dict) -> Optional[str]:
    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith((".exe", ".msi")) and ("setup" in name or "installer" in name):
            return asset.get("browser_download_url")
    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith((".exe", ".msi", ".zip")):
            return asset.get("browser_download_url")
    return None


def check_for_update() -> UpdateResult:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "PGame-Helper-Updater",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            release = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return {"ok": False, "error": "No GitHub release was found yet."}
        return {"ok": False, "error": f"GitHub returned HTTP {ex.code}."}
    except Exception as ex:
        return {"ok": False, "error": f"Could not check for updates: {ex}"}

    latest_version = str(release.get("tag_name") or release.get("name") or "").lstrip("vV")
    if not latest_version:
        return {"ok": False, "error": "The latest GitHub release has no version tag."}

    return {
        "ok": True,
        "current_version": APP_VERSION,
        "latest_version": latest_version,
        "update_available": is_newer_version(latest_version),
        "html_url": release.get("html_url"),
        "download_url": _asset_download_url(release),
        "release_name": release.get("name") or release.get("tag_name"),
    }


def check_for_update_async(callback: Callable[[UpdateResult], None]) -> None:
    def worker():
        callback(check_for_update())

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

