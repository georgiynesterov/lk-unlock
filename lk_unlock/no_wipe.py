import re


class NoWipePatch:
    def __init__(self, name, arch, pattern, replacement):
        self.name = name
        self.arch = arch
        self.pattern = pattern
        self.replacement = bytes.fromhex(replacement.replace(' ', ''))
        self.values, self.masks = self._parse(pattern)

    @staticmethod
    def _parse(pattern):
        pattern = re.sub(r'[\s:]', '', pattern)
        if len(pattern) % 2:
            raise ValueError('Pattern must contain whole bytes')

        values = bytearray()
        masks = bytearray()
        for i in range(0, len(pattern), 2):
            hi, lo = pattern[i], pattern[i + 1]
            value = mask = 0
            if hi != '?':
                value |= int(hi, 16) << 4
                mask |= 0xF0
            if lo != '?':
                value |= int(lo, 16)
                mask |= 0x0F
            values.append(value)
            masks.append(mask)

        return bytes(values), bytes(masks)

    def matches_at(self, data, offset):
        if offset + len(self.values) > len(data):
            return False

        for i in range(len(self.values)):
            if data[offset + i] & self.masks[i] != self.values[i] & self.masks[i]:
                return False

        return True

    def find_all(self, data):
        prefix = 0
        while prefix < len(self.masks) and self.masks[prefix] == 0xFF:
            prefix += 1
        if prefix < 3:
            prefix = 3

        anchor = self.values[:prefix]
        found = []
        pos = data.find(anchor)
        while pos != -1:
            if self.matches_at(data, pos):
                found.append(pos)
            pos = data.find(anchor, pos + 1)

        return found


_NO_WIPE_PATCHES = [
    NoWipePatch(
        'v1',
        '32-bit Thumb',
        'f0 b5 83 b0 ?? f? ?? ?? 43 1c 04 46 13 d0',
        '00 20 70 47',
    ),
    NoWipePatch(
        'v2-direct',
        '64-bit AArch64',
        'fd 7b be a9 f3 0b 00 f9 fd 03 00 91 '
        '?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? '
        '00 03 00 b4 02 10 40 f9 e1 03 1f aa f3 03 00 aa '
        '?? ?? ?? ?? 63 12 40 f9 1f 00 03 eb 21 03 00 54 e0 03 13 aa',
        '00 00 80 52 c0 03 5f d6',
    ),
    NoWipePatch(
        'v2-recovery (lk64)',
        '64-bit AArch64',
        '3f 23 03 d5 fd 7b bd a9 f5 0b 00 f9 f4 4f 02 a9 '
        'fd 03 00 91 00 00 81 52 ?? ?? ?? ?? 60 01 00 b5',
        '00 00 80 52 c0 03 5f d6',
    ),
    NoWipePatch(
        'v2-recovery (malachite)',
        '64-bit AArch64',
        'fd 7b be a9 f3 0b 00 f9 fd 03 00 91 '
        '00 00 81 52 ?? ?? ?? ?? 20 01 00 b5',
        '00 00 80 52 c0 03 5f d6',
    ),
    NoWipePatch(
        'v2-recovery (warhol)',
        '64-bit AArch64',
        '3f 23 03 d5 fd 7b be a9 f4 4f 01 a9 fd 03 00 91 '
        '00 00 81 52 ?? ?? ?? ?? 40 01 00 b5',
        '00 00 80 52 c0 03 5f d6',
    ),
]


def apply_no_wipe_patch(data):
    matches = []
    for patch in _NO_WIPE_PATCHES:
        for offset in patch.find_all(data):
            matches.append((patch, offset))

    if not matches:
        raise ValueError('No supported userdata wipe pattern found')
    if len(matches) > 1:
        details = ', '.join(f'{p.name}@0x{o:X}' for p, o in matches)
        raise ValueError(f'Expected exactly one match, found {len(matches)}: {details}')

    patch, offset = matches[0]
    end = offset + len(patch.replacement)
    return data[:offset] + patch.replacement + data[end:], patch, offset
