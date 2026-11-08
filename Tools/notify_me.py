"""notify_me.py - voice notification with stop support.

Reads phrase from UTF-8 file, speaks via PowerShell SAPI (SSML), repeats
with interval, stops when runtime/notify.stop appears or operator activity.

Contract (from DeepSeek notify_me, rewritten for v5):
- Reads --file <path> (UTF-8 text) or --text <text>.
- Lock: runtime/notify.lock (O_EXCL, stale PID check).
- Stop: runtime/notify.stop -> exits before each repeat.
- Activity: runtime/watchdog_indep.heartbeat fresh -> back off, then exit.
- Log: logs/runtime/notify.log.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

# Resolve root relative to this file (Tools/notify_me.py -> parent.parent)
ROOT = Path(__file__).resolve().parent.parent
STOP_FILE = ROOT / "runtime" / "notify.stop"
LOCK_FILE = ROOT / "runtime" / "notify.lock"
ACTIVITY_FILE = ROOT / "runtime" / "watchdog_indep.heartbeat"
LOG_FILE = ROOT / "logs" / "runtime" / "notify.log"
PHRASE_FILE = ROOT / "runtime" / "notify_phrase.txt"


def log(msg: str) -> None:
    line = "[" + time.strftime("%H:%M:%S") + "] " + msg
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def pid_alive(pid: int) -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "PID eq " + str(pid), "/NH"],
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace", creationflags=0x08000000)
        return str(pid) in (r.stdout or "")
    except Exception:
        return False


def acquire_lock() -> bool:
    if LOCK_FILE.exists():
        try:
            content = LOCK_FILE.read_text(encoding="utf-8", errors="replace").strip()
            pid = int(content) if content.isdigit() else 0
            age = time.time() - LOCK_FILE.stat().st_mtime
            alive = pid_alive(pid) if pid else False
            if not alive or age > 120:
                LOCK_FILE.unlink()
        except Exception:
            pass
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        return True
    except FileExistsError:
        return False
    except Exception:
        return False


def release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass


def speak(text: str, voice_name: str = "") -> tuple:
    PHRASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PHRASE_FILE.write_text(text, encoding="utf-8")
    esc_path = str(PHRASE_FILE).replace("'", "''")
    lines = [
        "Add-Type -AssemblyName System.Speech",
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer",
    ]
    if voice_name:
        ev = voice_name.replace("'", "''")
        lines.append("$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -eq '" + ev + "' } | Select-Object -First 1")
        lines.append("if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }")
    else:
        lines.append("$all = $s.GetInstalledVoices() | Where-Object { $_.Enabled }")
        lines.append("$v = $all | Where-Object { $_.VoiceInfo.Name -like '*Pavel*' } | Select-Object -First 1")
        lines.append("if (-not $v) { $v = $all | Where-Object { $_.VoiceInfo.Name -like '*Irina*' } | Select-Object -First 1 }")
        lines.append("if (-not $v) { $v = $all | Where-Object { $_.VoiceInfo.Culture.Name -eq 'ru-RU' } | Select-Object -First 1 }")
        lines.append("if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }")
    lines.append("$s.SetOutputToDefaultAudioDevice()")
    lines.append("$s.Rate = 0")
    lines.append("$s.Volume = 100")
    lines.append("$txt = (Get-Content -Raw -Encoding UTF8 '" + esc_path + "').Trim()")
    lines.append("$esc = [System.Security.SecurityElement]::Escape($txt)")
    lines.append("$ssml = '<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xml:lang=\"ru-RU\"><prosody pitch=\"-30%\" rate=\"-10%\">' + $esc + '</prosody></speak>'")
    lines.append("$s.SpeakSsml($ssml)")
    ps = "; ".join(lines)
    flags = 0x08000000 if sys.platform == "win32" else 0
    r = subprocess.run(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
        capture_output=True, text=True, timeout=60,
        encoding="utf-8", errors="replace", creationflags=flags)
    return r.returncode, (r.stdout or "")[:100], (r.stderr or "")[:300]


def activity_fresh(threshold: int = 60) -> bool:
    if not ACTIVITY_FILE.exists():
        return False
    return (time.time() - ACTIVITY_FILE.stat().st_mtime) < threshold


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="")
    ap.add_argument("--file", default="")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--voice", default="")
    args = ap.parse_args()

    text = ""
    if args.file:
        fp = Path(args.file)
        if fp.exists():
            text = fp.read_text(encoding="utf-8").strip()
    if not text and args.text:
        text = args.text
    if not text:
        text = "Джошуа на связи. Нужна помощь."
    if len(text) > 400:
        text = text[:400]

    if not acquire_lock():
        log("lock held, exit")
        return 0

    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
        log("start voice='" + args.voice + "' repeat=" + str(args.repeat) + " text=" + text[:80])
        for i in range(1, args.repeat + 1):
            if STOP_FILE.exists():
                log("stop file, exit")
                return 0
            log("speak " + str(i) + "/" + str(args.repeat))
            rc, out, err = speak(text, args.voice or "")
            log("speak rc=" + str(rc))
            if rc != 0 and err:
                log("speak err: " + err[:200])
            if i < args.repeat:
                slept = 0
                while slept < args.interval:
                    if STOP_FILE.exists():
                        log("stop file (in sleep), exit")
                        return 0
                    time.sleep(5)
                    slept += 5
                    if activity_fresh(60):
                        log("activity, back off 5 min")
                        for _ in range(60):
                            if STOP_FILE.exists():
                                return 0
                            time.sleep(5)
                        if activity_fresh(60):
                            log("still active, exit")
                            return 0
                        break
        log("done all repeats")
    finally:
        release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
