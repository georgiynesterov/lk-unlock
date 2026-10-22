import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from liblk.image import LkImage

from .cert_bypass import CertBypassMode, apply_cert_bypass
from .keys import get_keys
from .no_wipe import apply_no_wipe_patch


def patch_img(
    img_path: str,
    output_path: str = None,
    use_wrap: bool = False,
    no_wipe_block: bool = False,
):
    if output_path is None:
        img = Path(img_path)
        output_path = str(img.with_name(f"{img.stem}_patched{img.suffix}"))

    _, new_pub_key = get_keys()
    new_n_bytes = new_pub_key.public_numbers().n.to_bytes(256, byteorder='big')

    try:
        with open("xiaomi.pem", "rb") as f:
            old_pub_key = serialization.load_pem_public_key(f.read())
    except FileNotFoundError:
        print("[-] 'xiaomi.pem' file not found.")
        sys.exit(1)

    old_n_bytes = old_pub_key.public_numbers().n.to_bytes(256, byteorder='big')
    try:
        with open(img_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"[-] '{img_path}' file not found.")
        sys.exit(1)

    pos = data.find(old_n_bytes)

    if pos == -1:
        print("[-] Error: Xiaomi's public key modulus not found in LK image. Nothing to patch.")
        sys.exit(1)

    print(f"[+] Original key modulus found at offset 0x{pos:X}")

    patched_data = data[:pos] + new_n_bytes + data[pos + len(new_n_bytes):]

    print(f"[+] Public key patched successfully")

    if no_wipe_block:
        print("[+] Userdata wipe patch disabled by --no-wipe-block")
    else:
        try:
            patched_data, no_wipe_patch, no_wipe_offset = apply_no_wipe_patch(patched_data)
            print(
                f"[+] Userdata wipe patch applied: {no_wipe_patch.name} "
                f"at 0x{no_wipe_offset:X}"
            )
        except ValueError as exc:
            print(f"[-] Failed to apply userdata wipe patch: {exc}")
            sys.exit(1)

    try:
        image = LkImage(patched_data)
        cert_bypass_mode = CertBypassMode.WRAP if use_wrap else CertBypassMode.OVERRIDE
        print(f"[+] Selected cert bypass mode: {cert_bypass_mode.value}")
        signed = apply_cert_bypass(image, cert_bypass_mode)
        if signed:
            patched_data = bytes(image.contents)
            print(f"[+] Cert bypass completed for: {', '.join(signed)}")
        else:
            print("[+] Cert bypass was not needed")
    except Exception as exc:
        print(f"[-] Failed to apply cert bypass: {exc}")
        sys.exit(1)

    with open(output_path, "wb") as f:
        f.write(patched_data)

    print(f"[+] All done! Lk saved to: {output_path}")
