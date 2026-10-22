import re
import subprocess
import sys

from .sign import sign_token


def run_fastboot(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    command = ["fastboot", *args]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        print("[-] fastboot binary not found. Put it in the program folder or add it to PATH.")
        sys.exit(1)
    except OSError as exc:
        print(f"[-] Failed to run fastboot: {exc}")
        sys.exit(1)

    if result.returncode != 0 and check:
        error_text = (result.stderr or result.stdout).strip()
        if error_text:
            print(f"[-] Fastboot command failed: {' '.join(args)}")
            print(error_text)
        else:
            print(f"[-] Fastboot command failed: {' '.join(args)}")
        sys.exit(1)

    return result


def extract_token(output: str) -> str:
    token_lines = []

    for line in output.splitlines():
        match = re.match(r"^(?:\(bootloader\)\s+)?token:\s*(.+)$", line.strip(), re.IGNORECASE)
        if match:
            token_lines.append(match.group(1).strip())

    if token_lines:
        return "".join(token_lines)

    return ""


def unlock_device(dry_run: bool = False):
    print("[+] Looking for fastboot devices...")
    devices_result = run_fastboot("devices")
    devices = [line.strip().split(" ")[0] for line in devices_result.stdout.splitlines() if line.strip()]

    if not devices:
        print("[-] No fastboot devices found.")
        sys.exit(1)

    print(f"[+] Device found: {devices[0]}")

    print("[+] Reading unlock token...")
    token_result = run_fastboot("oem", "get_token", check=False)
    token_output = (token_result.stdout or "") + (token_result.stderr or "")

    if "unknown command" in token_output.lower():
        print("[+] 'oem get_token' is not supported, retrying with 'getvar token'")
        token_result = run_fastboot("getvar", "token")
        token_output = (token_result.stdout or "") + (token_result.stderr or "")
    elif token_result.returncode != 0:
        error_text = (token_result.stderr or token_result.stdout).strip()
        print("[-] Fastboot command failed: oem get_token")
        if error_text:
            print(error_text)
        sys.exit(1)

    token = extract_token(token_output)

    if not token:
        print("[-] Failed to extract token from fastboot output.")
        sys.exit(1)

    print(f"[+] Token received: {token}")

    print("[+] Signing token...")
    sign_token(token)

    if dry_run:
        print("[+] Dry run enabled. Skipping fastboot stage and fastboot oem unlock")
        return

    print("[+] Uploading signature.bin to device...")
    run_fastboot("stage", "signature.bin")

    print("[+] Sending unlock command...")
    run_fastboot("oem", "unlock")

    print("[+] Device unlock command completed successfully")
