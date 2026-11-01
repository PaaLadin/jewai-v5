"""Tools/voice_call.py - голосовой вызов оператора с защитой (громкость/ночь)."""
import subprocess
import time
import sys

def get_volume():
    try:
        ps = "Add-Type -AssemblyName CoreAudioApi; (New-Object CoreAudioApi.MMDeviceEnumerator).GetDefaultAudioEndpoint(0,1).AudioEndpointVolume.MasterVolumeLevelScalar * 100"
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True, timeout=10)
        return int(float(r.stdout.strip() or "100"))
    except Exception:
        return 100

def set_volume(val):
    try:
        ps = f"(Get-AudioDevice -PlaybackVolume).Volume = {val}"
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, timeout=10)
    except Exception:
        pass

def speak(text):
    try:
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate = 1; "
            f"$s.Speak('{text}')"
        )
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, timeout=20)
        return True
    except Exception:
        return False

def call_operator(message="Оператор, я закончил. Жду вас."):
    vol = get_volume()
    hour = time.localtime().tm_hour
    night = (hour >= 22) or (hour < 8)

    print(f"[voice_call] Volume={vol}%, Hour={hour}, Night={night}")

    if vol < 5:
        if night:
            print("[voice_call] Skipped: Mute + Night.")
            return False
        else:
            print("[voice_call] Mute + Day. Raising volume to 15.")
            set_volume(15)
            time.sleep(1)

    print("[voice_call] Speaking...")
    return speak(message)

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Оператор, я закончил. Жду вас."
    call_operator(msg)
