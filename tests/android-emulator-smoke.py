#!/usr/bin/env python3
"""Reliable Android emulator smoke test for app startup and native progress persistence.

The emulator action's script input is safest as one command. Keep polling and
multi-step shell control flow in Python rather than embedding compound shell loops.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Callable

PACKAGE = "com.stepuparabic.app"
ACTIVITY = "com.stepuparabic.app/.MainActivity"
SAVE_FILE = "files/stepuparabic-progress.json"
WAIT_SECONDS = 90


def adb(*args: str, timeout: int = 40, check: bool = True) -> str:
    result = subprocess.run(
        ["adb", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    output = result.stdout or ""
    if check and result.returncode != 0:
        raise RuntimeError(
            f"adb {' '.join(args)} failed (exit {result.returncode}):\n{output[-5000:]}"
        )
    return output.strip()


def wait_for_log(predicate: Callable[[str], bool], label: str) -> str:
    deadline = time.monotonic() + WAIT_SECONDS
    latest = ""
    while time.monotonic() < deadline:
        latest = adb("logcat", "-d", "-s", "StepUpArabic:I", "AndroidRuntime:E", timeout=30)
        if predicate(latest):
            print(f"PASS: {label}")
            return latest
        time.sleep(2)
    relevant = "\n".join(
        line for line in latest.splitlines()
        if any(token in line for token in ("StepUpArabic", "chromium", "AndroidRuntime"))
    )
    raise RuntimeError(
        f"Timed out after {WAIT_SECONDS}s waiting for {label}. Recent app logs:\n"
        + (relevant[-12000:] or "(no StepUpArabic log entries were emitted)")
    )


def read_saved_progress() -> dict:
    raw = adb("shell", "run-as", PACKAGE, "cat", SAVE_FILE, timeout=30)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Native progress file is not valid JSON: {error}\n{raw[:2000]}")
    if "ms-a1" not in value.get("completed", []):
        raise RuntimeError("Native save file is missing the smoke-test lesson ms-a1")
    if value.get("preferences", {}).get("activeTrack") != "spoken":
        raise RuntimeError("Native save file did not preserve the spoken active track")
    return value


def main() -> int:
    print("Waiting for Android emulator...")
    adb("wait-for-device", timeout=120)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if adb("shell", "getprop", "sys.boot_completed", timeout=20, check=False) == "1":
            break
        time.sleep(2)
    else:
        raise RuntimeError("Android emulator did not finish booting")

    print("Installing current APK...")
    adb("install", "-r", "android/app/build/outputs/apk/debug/app-debug.apk", timeout=180)
    adb("logcat", "-c")
    adb("shell", "am", "start", "-n", ACTIVITY, "--ez", "stepup_smoke", "true")
    pid = adb("shell", "pidof", PACKAGE, timeout=20)
    if not pid:
        raise RuntimeError("App process did not remain running after launch")
    activity_list = adb("shell", "dumpsys", "activity", "activities", timeout=30)
    if ACTIVITY not in activity_list:
        raise RuntimeError("MainActivity did not become the foreground activity")

    first_logs = wait_for_log(
        lambda logs: "SAVE_PROGRESS_SUCCESS:" in logs,
        "first native progress save",
    )
    print("\n".join(line for line in first_logs.splitlines() if "StepUpArabic" in line)[-30:])
    first_state = read_saved_progress()
    print(
        "PASS: first save contains lesson ms-a1 and activeTrack=spoken "
        f"({len(first_state.get('completed', []))} completed lessons)"
    )

    print("Restarting app to verify restore...")
    adb("shell", "am", "force-stop", PACKAGE)
    adb("logcat", "-c")
    adb("shell", "am", "start", "-n", ACTIVITY, "--ez", "stepup_smoke", "true")
    second_logs = wait_for_log(
        lambda logs: '"restored":true' in logs and "SAVE_SMOKE:" in logs,
        "progress restore after force-stop and restart",
    )
    print("\n".join(line for line in second_logs.splitlines() if "StepUpArabic" in line)[-30:])
    second_state = read_saved_progress()
    print(
        "PASS: restarted app retained lesson ms-a1 and activeTrack=spoken "
        f"({len(second_state.get('completed', []))} completed lessons)"
    )

    fatal = adb("logcat", "-d", "-s", "AndroidRuntime:E", timeout=30)
    if "FATAL EXCEPTION" in fatal:
        raise RuntimeError("AndroidRuntime reported a fatal exception:\n" + fatal[-8000:])

    print("ANDROID_SMOKE_TEST_PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ANDROID_SMOKE_TEST_FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
