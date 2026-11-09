"""Tools/get_cft.py - download Chrome for Testing (CfT) to tools/chrome-for-testing/.

Chrome 137+ ignores --load-extension for unpacked extensions (BUG-009 / B-44).
The only way to load our sidepanel/onboarding extension is CfT.
This script downloads the latest stable CfT (~448 MB) from Google's official CDN
and extracts it in place.

Usage:
  python Tools/get_cft.py                          # download latest to <repo>/tools/chrome-for-testing
  python Tools/get_cft.py --version 158.0.8127.2   # pin version
  python Tools/get_cft.py --dest <path>            # custom destination (used by installer)
  python Tools/get_cft.py --force                  # re-download even if present
  python Tools/get_cft.py --check                  # exit 0 if present, 1 if not
  python Tools/get_cft.py --dry-run                # show version+URL, don't download
  python Tools/get_cft.py --url <url>              # custom zip URL (for testing)

Exit codes: 0=ok/already present, 1=not present (--check), 2=download/extract failed.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_DEST = Path(__file__).resolve().parent.parent / "tools" / "chrome-for-testing"
META_URL = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
CDN_BASE = "https://storage.googleapis.com/chrome-for-testing-public"
USER_AGENT = "jewai-installer/1.0"


def _log(msg: str) -> None:
    print(msg, flush=True)


def _fetch_meta(version: str | None) -> tuple[str, str]:
    """Return (version, zip_url) for win64 chrome. version=None -> latest stable."""
    _log("fetch metadata: %s" % META_URL)
    req = urllib.request.Request(META_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    channels = data.get("channels") or {}
    if version:
        # find in any channel
        for _ch, spec in channels.items():
            if str(spec.get("version")) == str(version):
                for d in (spec.get("downloads") or {}).get("chrome", []):
                    if d.get("platform") == "win64":
                        return version, d["url"]
        # fallback: construct URL
        return version, "%s/%s/win64/chrome-win64.zip" % (CDN_BASE, version)
    stable = channels.get("Stable") or {}
    ver = str(stable.get("version") or "")
    if not ver:
        raise RuntimeError("no Stable version in metadata")
    for d in (stable.get("downloads") or {}).get("chrome", []):
        if d.get("platform") == "win64":
            return ver, d["url"]
    return ver, "%s/%s/win64/chrome-win64.zip" % (CDN_BASE, ver)


def _download(url: str, out_path: Path) -> None:
    _log("download: %s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r, open(out_path, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        last_pct = -10
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if total:
                pct = int(got * 100 / total)
                if pct >= last_pct + 10:
                    _log("  %d%% (%d/%d MB)" % (pct, got // (1024 * 1024), total // (1024 * 1024)))
                    last_pct = pct
    dt = time.time() - t0
    mb = got / (1024 * 1024)
    _log("download done: %.1f MB in %.1fs (%.1f MB/s)" % (mb, dt, mb / max(dt, 0.1)))


def _extract(zip_path: Path, dest: Path) -> None:
    _log("extract: %s -> %s" % (zip_path.name, dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_extract = dest.parent / "_cft_extract_tmp"
    if tmp_extract.exists():
        shutil.rmtree(tmp_extract, ignore_errors=True)
    tmp_extract.mkdir(parents=True)
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp_extract)
        # zip contains a single top dir: chrome-win64/
        candidates = [p for p in tmp_extract.iterdir() if p.is_dir()]
        src_dir = None
        for c in candidates:
            if (c / "chrome.exe").exists():
                src_dir = c
                break
        if src_dir is None:
            raise RuntimeError("no chrome.exe found in extracted tree; contents: %s"
                               % [str(c.name) for c in candidates])
        if dest.exists():
            shutil.rmtree(dest)
        src_dir.rename(dest)
        _log("extracted -> %s" % dest)
    finally:
        shutil.rmtree(tmp_extract, ignore_errors=True)


def _verify(dest: Path) -> Path:
    exe = dest / "chrome.exe"
    if not exe.exists():
        raise RuntimeError("chrome.exe not found in %s" % dest)
    return exe


def cmd_check(dest: Path) -> int:
    exe = dest / "chrome.exe"
    if exe.exists():
        mb = exe.stat().st_size / (1024 * 1024)
        _log("OK: CfT present at %s (%.1f MB)" % (exe, mb))
        return 0
    _log("MISS: no chrome.exe at %s" % exe)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=None, help="CfT version (default: latest stable)")
    ap.add_argument("--dest", default=str(DEFAULT_DEST))
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    ap.add_argument("--check", action="store_true", help="exit 0 if present, 1 if not")
    ap.add_argument("--dry-run", action="store_true", help="show version+URL, don't download")
    ap.add_argument("--url", default=None, help="custom zip URL (for testing)")
    a = ap.parse_args()

    dest = Path(a.dest)

    if a.check:
        return cmd_check(dest)

    exe = dest / "chrome.exe"
    if exe.exists() and not a.force:
        mb = exe.stat().st_size / (1024 * 1024)
        _log("OK: CfT already present at %s (%.1f MB) - skip download" % (exe, mb))
        return 0

    try:
        if a.url:
            url = a.url
            version = a.version or "custom"
        else:
            version, url = _fetch_meta(a.version)
        _log("CfT version: %s" % version)
        _log("CfT URL: %s" % url)
        if a.dry_run:
            _log("DRY-RUN: would download and extract to %s" % dest)
            return 0

        dest.parent.mkdir(parents=True, exist_ok=True)
        zip_path = dest.parent / "chrome-win64.zip"
        try:
            _download(url, zip_path)
            _extract(zip_path, dest)
        finally:
            try:
                zip_path.unlink()
            except Exception:
                pass
        _verify(dest)
        _log("OK: CfT ready at %s" % exe)
        return 0
    except Exception as e:
        _log("FAIL: %r" % e)
        _log("  If behind a firewall, download chrome-win64.zip manually:")
        _log("  https://googlechromelabs.github.io/chrome-for-testing/")
        _log("  Extract to: %s" % dest)
        return 2


if __name__ == "__main__":
    sys.exit(main())