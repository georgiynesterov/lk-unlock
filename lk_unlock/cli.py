import argparse

from .fastboot import unlock_device
from .patch import patch_img
from .sign import sign_token


def main():
    parser = argparse.ArgumentParser(description="Unlocking Xiaomi mtk bootloader by patching the public key.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    patch_parser = subparsers.add_parser("patch", help="Patch lk.img")
    patch_parser.add_argument("img", help="lk.img file path")
    patch_parser.add_argument("-o", "--output", help="Output file path", default=None)
    patch_parser.add_argument("--wrap", action="store_true", help="Use wrap mode for cert bypass")
    patch_parser.add_argument(
        "--no-wipe-block",
        action="store_true",
        help="Disable the userdata wipe patch",
    )

    sign_parser = subparsers.add_parser("sign", help="Sign the token")
    sign_parser.add_argument("token", help="Token string")

    unlock_parser = subparsers.add_parser("unlock", help="Unlock patched device automatically")
    unlock_parser.add_argument("--dry-run", action="store_true", help="Read and sign token, but skip stage and unlock")

    args = parser.parse_args()

    print("[*] LK-Unlock v1.0 by @georgiynesterov")

    if args.command == "patch":
        patch_img(args.img, args.output, args.wrap, args.no_wipe_block)
    elif args.command == "sign":
        sign_token(args.token)
    elif args.command == "unlock":
        unlock_device(args.dry_run)
