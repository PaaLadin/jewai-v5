"""Tools/voice_call.py - голосовой вызов оператора с защитой (громкость/ночь)."""
import subprocess
import time
import sys

PS_GET_VOLUME = """
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
  int NotImpl1(); int NotImpl2(); int GetChannelCount(out uint pnChannelCount);
  int SetMasterVolumeLevel(float fLevelDB, System.Guid pguidEventContext);
  int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
  int GetMasterVolumeLevel(out float pfLevelDB);
  int GetMasterVolumeLevelScalar(out float pfLevel);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
  int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
  int f(); int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject { }
public class Audio {
  static IAudioEndpointVolume Vol() {
    var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
    IMMDevice dev = null;
    enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
    IAudioEndpointVolume epv = null;
    var epvid = typeof(IAudioEndpointVolume).GUID;
    dev.Activate(ref epvid, 23, 0, out epv);
    return epv;
  }
  public static float GetVolume() { float v; Vol().GetMasterVolumeLevelScalar(out v); return v * 100; }
  public static void SetVolume(float v) { Vol().SetMasterVolumeLevelScalar(v / 100f, System.Guid.Empty); }
}
'@
"""

def run_ps(script):
    return subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True, timeout=10)

def get_volume():
    try:
        r = run_ps(PS_GET_VOLUME + "\n[Audio]::GetVolume()")
        return int(float(r.stdout.strip()))
    except Exception:
        return -1

def set_volume(val):
    try:
        run_ps(PS_GET_VOLUME + f"\n[Audio]::SetVolume({val})")
        return True
    except Exception:
        return False

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

    if vol == -1:
        print("[voice_call] Cannot read volume. Proceeding with speech.")
    elif vol < 5:
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
