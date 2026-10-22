from enum import Enum
from typing import List

from liblk.image import LkImage
from liblk.structures.certificate import Certificate
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1.type.univ import BitString


class CertBypassMode(str, Enum):
    WRAP = 'wrap'
    OVERRIDE = 'override'


def build_bypass_cert2_wrap(
    original_cert2: bytes, header_hash: bytes, image_hash: bytes
) -> bytes:
    cert = Certificate.from_bytes(original_cert2)
    verified_copy = der_encode(BitString(hexValue=bytes(original_cert2).hex()))
    forged_copy = cert.encode_with_hashes(header_hash, image_hash)
    return verified_copy + forged_copy


def build_bypass_cert2_override(
    original_cert2: bytes, header_hash: bytes, image_hash: bytes
) -> bytes:
    cert = Certificate.from_bytes(original_cert2)
    override = cert.build_hash_override_block(header_hash, image_hash)
    return override + bytes(original_cert2)


_CERT_BUILDERS = {
    CertBypassMode.WRAP: build_bypass_cert2_wrap,
    CertBypassMode.OVERRIDE: build_bypass_cert2_override,
}


def apply_cert_bypass(
    image: LkImage, mode: CertBypassMode = CertBypassMode.OVERRIDE
) -> List[str]:
    build = _CERT_BUILDERS[CertBypassMode(mode)]
    signed = []

    for name, partition in image.partitions.items():
        if partition.cert2 is None:
            continue

        status = partition.matches_cert2()

        if status is None:
            print(f"[-] Partition '{name}' cert2 could not be parsed. Skipping cert bypass.")
            continue

        if status:
            continue

        header_hash, image_hash = partition.compute_hashes()
        original = bytes(partition.cert2.data)
        partition.cert2.data = build(original, header_hash, image_hash)

        print(
            f"[+] Cert bypass applied to partition '{name}' "
            f"({CertBypassMode(mode).value}, cert2 {len(original)} -> {len(partition.cert2.data)} bytes)"
        )
        signed.append(name)

    if signed:
        image._rebuild_contents()

    return signed
