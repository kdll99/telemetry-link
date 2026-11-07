"""Decode fixed 32-byte UDP telemetry packets (big-endian).

Packet layout matches the Telemetry M1 packet spec:
  sync(u16) seq(u32) timestamp_ms(u64) altitude_m(f32)
  velocity_mps(f32) heading_deg(f32) status(u16) checksum(u32)
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import Optional

PACKET_SIZE = 32
SYNC_WORD = 0xA55A
# > H I Q f f f H I  == uint16, uint32, uint64, 3x float32, uint16, uint32
UNPACK_FMT = ">HIQfffHI"
HEADER_BYTES = 28  # bytes covered by the CRC32 checksum field


@dataclass(frozen=True)
class TelemetryPacket:
    sync: int
    seq: int
    timestamp_ms: int
    altitude_m: float
    velocity_mps: float
    heading_deg: float
    status: int
    checksum: int


class DecodeError(ValueError):
    """Raised when a datagram fails length, sync, or checksum checks."""


def crc32_header(data: bytes) -> int:
    if len(data) < HEADER_BYTES:
        raise DecodeError(f"need at least {HEADER_BYTES} bytes for CRC, got {len(data)}")
    return zlib.crc32(data[:HEADER_BYTES]) & 0xFFFFFFFF


def decode_packet(data: bytes) -> TelemetryPacket:
    if len(data) != PACKET_SIZE:
        raise DecodeError(f"expected {PACKET_SIZE} bytes, got {len(data)}")

    sync, seq, timestamp_ms, altitude_m, velocity_mps, heading_deg, status, checksum = (
        struct.unpack(UNPACK_FMT, data)
    )

    if sync != SYNC_WORD:
        raise DecodeError(f"bad sync 0x{sync:04X}, expected 0x{SYNC_WORD:04X}")

    expected = crc32_header(data)
    if checksum != expected:
        raise DecodeError(
            f"checksum mismatch: packet=0x{checksum:08X} computed=0x{expected:08X}"
        )

    return TelemetryPacket(
        sync=sync,
        seq=seq,
        timestamp_ms=timestamp_ms,
        altitude_m=altitude_m,
        velocity_mps=velocity_mps,
        heading_deg=heading_deg,
        status=status,
        checksum=checksum,
    )


def build_packet(
    seq: int,
    timestamp_ms: int,
    altitude_m: float,
    velocity_mps: float,
    heading_deg: float,
    status: int = 0,
) -> bytes:
    """Build a valid 32-byte packet (useful for decoder self-tests)."""
    body = struct.pack(
        ">HIQfffH",
        SYNC_WORD,
        seq,
        timestamp_ms,
        altitude_m,
        velocity_mps,
        heading_deg,
        status,
    )
    checksum = zlib.crc32(body) & 0xFFFFFFFF
    return body + struct.pack(">I", checksum)


class DropTracker:
    """Count sequence gaps (dropped packets) across a stream."""

    def __init__(self) -> None:
        self._last_seq: Optional[int] = None
        self.received = 0
        self.dropped = 0

    def observe(self, seq: int) -> int:
        """Return how many packets were skipped since the previous seq."""
        skipped = 0
        if self._last_seq is not None and seq > self._last_seq + 1:
            skipped = seq - self._last_seq - 1
            self.dropped += skipped
        self._last_seq = seq
        self.received += 1
        return skipped
