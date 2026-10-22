import sys

from cryptography.hazmat.primitives import serialization


def encode(token: bytes) -> bytes:
    if len(token) > 253:
        raise ValueError("Bad token")
    ps = b'\xff' * (256 - len(token) - 3)
    return b'\x00\x01' + ps + b'\x00' + token


def sign_token(token: bytes):
    if isinstance(token, str):
        token = token.encode()

    try:
        with open("private.pem", "rb") as f:
            priv = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
    except FileNotFoundError:
        print("[-] private.pem file not found. Please run 'patch' command first.")
        sys.exit(1)

    numbers = priv.private_numbers()
    n = numbers.public_numbers.n
    d = numbers.d

    em = encode(token)
    m = int.from_bytes(em, "big")
    s = pow(m, d, n)
    signature = s.to_bytes(256, "big")

    with open("signature.bin", "wb") as f:
        f.write(signature)

    print("[+] The token signature was successfully generated and saved to 'signature.bin'")
