"""Generate simple solid-color PNG icons for the PWA (pure stdlib, no Pillow)."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

OUT = Path("app/training_static/icons")
OUT.mkdir(parents=True, exist_ok=True)

BG = (15, 23, 42)  # #0f172a
ACCENT = (99, 102, 241)  # #6366f1


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def make_icon(size: int, path: Path) -> None:
    # RGBA pixel buffer
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            # Draw a simple "bar chart" motif (3 vertical bars).
            bar_w = size // 6
            gap = size // 8
            base_y = size - size // 4
            bar1_x0 = size // 4
            bar2_x0 = size // 2 - bar_w // 2
            bar3_x0 = 3 * size // 4 - bar_w
            bars = [
                (bar1_x0, bar1_x0 + bar_w, size // 2),
                (bar2_x0, bar2_x0 + bar_w, size // 3),
                (bar3_x0, bar3_x0 + bar_w, size // 4),
            ]
            color = BG
            for (x0, x1, top) in bars:
                if x0 <= x < x1 and top <= y < base_y:
                    color = ACCENT
                    break
            row += bytes((color[0], color[1], color[2], 255))
        rows.append(bytes(row))

    raw = b"".join(b"\x00" + r for r in rows)  # filter byte 0 per scanline

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    print(f"wrote {path} ({size}x{size})")


if __name__ == "__main__":
    make_icon(192, OUT / "icon-192.png")
    make_icon(512, OUT / "icon-512.png")
