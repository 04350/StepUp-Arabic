#!/usr/bin/env python3
"""Install and launch-test the non-debuggable, signed release APK.

The detailed native-save test stays on the debuggable variant because Android
intentionally blocks adb run-as access to private files in release builds.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

PACKAGE = "com.stepuparabic.app"
ACTIVITY = "com.stepuparabic.app/.MainActivity"
APK_PATH = os.environ.get("STEPUP_RELEASE_APK_PATH", "").strip()


def adb(*args: str, timeout: int = 45, check: bool = True) -> str:
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
            f"adb {' '.join(args)} failed (exit {result.returncode}):\\n{output[-5000:]}"
        )
    return output.strip()


def main() -> int:
    if not APK_PATH:
        print("SKIP: no signed Release APK is produced for pull-request builds")
        return 0
    if not os.path.isfile(APK_PATH):
        raise RuntimeError(f"Release APK does not exist: {APK_PATH}")

    print(f"Installing signed Release APK: {APK_PATH}")
    adb("install", "-r", APK_PATH, timeout=180)
    adb("logcat", "-c")
    launch_output = adb("shell", "am", "start", "-W", "-n", ACTIVITY, timeout=60)
    print("Launch result: " + launch_output)

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        pid = adb("shell", "pidof", PACKAGE, timeout=20, check=False)
        activities = adb("shell", "dumpsys", "activity", "activities", timeout=30, check=False)
        if pid and ACTIVITY in activities:
            break
        time.sleep(2)
    else:
        logs = adb("logcat", "-d", "-s", "AndroidRuntime:E", "ActivityManager:E", timeout=30)
        raise RuntimeError(
            "Signed Release APK did not remain in the foreground.\\n"
            + launch_output + "\\n" + logs[-10000:]
        )

    fatal = adb("logcat", "-d", "-s", "AndroidRuntime:E", timeout=30)
    if "FATAL EXCEPTION" in fatal:
        raise RuntimeError("Release APK caused a fatal Android exception:\\n" + fatal[-8000:])

    print("PASS: signed, non-debuggable Release APK installed and launched")
    print("ANDROID_RELEASE_SMOKE_TEST_PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ANDROID_RELEASE_SMOKE_TEST_FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
