"""Core/config.py — конфигурация v5. Единственный источник правды о портах, каналах, путях.

Правила:
- Никакого хардкода путей. Всё через Config.root().
- Никакой глобальной изменяемости. Один экземпляр на процесс, доступ через Config.load().
- config.json — данные, не код. Должен читаться без импортов.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Channel:
    letter: str
    name: str
    agent_port: int
    cdp_port: int
    prefix: str
    extension: str
    model: str


@dataclass(frozen=True)
class Config:
    root: Path
    bind: str
    chat_port: int
    doh_proxy_port: int
    letters: tuple[str, ...]
    channels: dict[str, Channel] = field(default_factory=dict)
    thresholds: dict[str, int] = field(default_factory=dict)
    timeouts: dict[str, int] = field(default_factory=dict)
    version: str = ""

    def channel(self, letter: str) -> Channel:
        ch = self.channels.get(letter.upper())
        if not ch:
            raise KeyError(f"unknown channel: {letter!r}")
        return ch

    def channel_by_cdp(self, cdp_port: int) -> Channel | None:
        for ch in self.channels.values():
            if ch.cdp_port == cdp_port:
                return ch
        return None

    def channel_by_agent(self, agent_port: int) -> Channel | None:
        for ch in self.channels.values():
            if ch.agent_port == agent_port:
                return ch
        return None

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def channel_root(self, letter: str) -> Path:
        """Per-agent root: <root>/Profiles/<L>."""
        return self.root / "Profiles" / letter.upper()

    def channel_path(self, letter: str, *parts: str) -> Path:
        """Per-agent path: <root>/Profiles/<L>/<parts...>."""
        return self.channel_root(letter).joinpath(*parts)

    def channel_config(self, letter: str) -> dict:
        """Load per-agent config: Profiles/<L>/config/config.json."""
        p = self.channel_path(letter, "config", "config.json")
        if not p.exists():
            return {}
        import json as _json
        return _json.loads(p.read_text(encoding="utf-8"))



# ---- загрузка ----

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load(config_path: Path | str | None = None) -> Config:
    """Загрузить конфиг. Путь: аргумент > env JEWAI_CONFIG > C:/JewAI/config.json."""
    import os

    p = Path(config_path) if config_path else Path(os.environ.get("JEWAI_CONFIG", _DEFAULT_CONFIG_PATH))
    if not p.exists():
        raise FileNotFoundError(f"config.json not found: {p}")

    data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    root = Path(data["root"]).resolve()

    channels: dict[str, Channel] = {}
    for letter, spec in data.get("channels", {}).items():
        channels[letter.upper()] = Channel(
            letter=letter.upper(),
            name=spec["name"],
            agent_port=int(spec["agent"]),
            cdp_port=int(spec["cdp"]),
            prefix=spec["prefix"],
            extension=spec.get("extension", "extension"),
            model=spec.get("model", "deepseek"),
        )

    letters = tuple(data.get("letters", channels.keys()))

    return Config(
        root=root,
        bind=str(data.get("bind", "127.0.0.1")),
        chat_port=int(data.get("chat_port", 8670)),
        doh_proxy_port=int(data.get("doh_proxy_port", 9899)),
        letters=letters,
        channels=channels,
        thresholds=dict(data.get("thresholds", {})),
        timeouts=dict(data.get("timeouts", {})),
        version=str(data.get("version", "")),
    )