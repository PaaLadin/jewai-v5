"""Mainframe/mail.py - SMTP.

9C (2026-11-09): SMTP settings moved OUT of config.json into .secret/smtp.json.
Reason: config.json was tracked in git - would leak. Now config is gitignored,
and secrets live in .secret/ (also gitignored).

Contract:
- Reads .secret/smtp.json: {smtp_host, smtp_port, from_addr, password, to_addr, use_tls}
- Falls back to config.mail (deprecated, will be removed 2026-Q1).
- status(cfg) -, configured, source}
- send(cfg, subject, body) -, error?}
- Never logs password.
"""
from __future__ import annotations
import json, smtplib
from email.mime.text import MIMEText
from typing import Any
from Core.config import Config


def _load_secret(cfg: Config) -> dict[str, Any]:
    p = cfg.path(".secret", "smtp.json")
    if not p.exists():
        return {}
    try:
        return dict(json.loads(p.read_text(encoding="utf-8")) or {})
    except Exception:
        return {}


def _load_config_legacy(cfg: Config) -> dict[str, Any]:
    try:
        data = json.loads(cfg.path("config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(data.get("mail") or {})


def _mail_cfg(cfg: Config) -> tuple[dict[str, Any], str]:
    sec = _load_secret(cfg)
    if sec:
        return sec, "secret"
    legacy = _load_config_legacy(cfg)
    if legacy:
        return legacy, "config_legacy"
    return {}, "none"


def status(cfg: Config) -> dict:
    c, src = _mail_cfg(cfg)
    ok = bool(c.get("smtp_host") and c.get("from_addr") and c.get("to_addr"))
    return {"ok": True, "configured": ok, "source": src,
            "host": c.get("smtp_host", ""),
            "port": c.get("smtp_port", 587),
            "reason": "" if ok else "not_configured (create .secret/smtp.json)"}


def send(cfg: Config, subject: str, body: str) -> dict:
    c, src = _mail_cfg(cfg)
    if not (c.get("smtp_host") and c.get("from_addr") and c.get("to_addr")):
        return {"ok": False, "error": "mail not configured"}
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = c["from_addr"]
    msg["To"] = c["to_addr"]
    try:
        with smtplib.SMTP(c["smtp_host"], int(c.get("smtp_port", 587)), timeout=30) as s:
            s.ehlo()
            if c.get("use_tls", True):
                s.starttls()
                s.ehlo()
            if c.get("password"):
                s.login(c["from_addr"], c["password"])
            s.send_message(msg)
        return {"ok": True, "source": src}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)[:200]}
