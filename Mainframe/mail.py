"""Mainframe/mail.py - SMTP mail stub (Ф5).

Contract:
- Config keys: mail: {smtp_host, smtp_port, from_addr, password, to_addr}
- status(cfg) -> {ok, configured}
- send(cfg, subject, body) -> {ok, error?}
- If not configured: {ok:false, reason:"not_configured"}.
- Uses smtplib with STARTTLS. Never logs password.
"""
from __future__ import annotations

import json
import smtplib
from email.mime.text import MIMEText
from typing import Any

from Core.config import Config


def _mail_cfg(cfg: Config) -> dict[str, Any]:
    try:
        data = json.loads(cfg.path("config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(data.get("mail") or {})


def status(cfg: Config) -> dict:
    c = _mail_cfg(cfg)
    ok = bool(c.get("smtp_host") and c.get("from_addr") and c.get("to_addr"))
    return {"ok": True, "configured": ok,
            "host": c.get("smtp_host", ""),
            "port": c.get("smtp_port", 587),
            "reason": "" if ok else "not_configured (set config.mail)"}


def send(cfg: Config, subject: str, body: str) -> dict:
    c = _mail_cfg(cfg)
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
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)[:200]}