from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def get_keys():
    private_key_path = Path("private.pem")
    public_key_path = Path("public.pem")

    if private_key_path.exists() and public_key_path.exists():
        with private_key_path.open("rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )

        with public_key_path.open("rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        print("[+] Existing keys found. Using private.pem and public.pem")
        return private_key, public_key

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    with private_key_path.open("wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    public_key = private_key.public_key()
    with public_key_path.open("wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print("[+] New keys have been generated and saved into private.pem and public.pem")
    return private_key, public_key
