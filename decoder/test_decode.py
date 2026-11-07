"""Self-test for the M1 packet decoder (no network required)."""

from __future__ import annotations

import struct
import zlib

from decode import (
    PACKET_SIZE,
    SYNC_WORD,
    DecodeError,
    DropTracker,
    build_packet,
    decode_packet,
)


def test_round_trip() -> None:
    raw = build_packet(
        seq=7,
        timestamp_ms=1_700_000_000_000,
        altitude_m=1234.5,
        velocity_mps=67.25,
        heading_deg=359.0,
        status=0x0001,
    )
    assert len(raw) == PACKET_SIZE
    pkt = decode_packet(raw)
    assert pkt.sync == SYNC_WORD
    assert pkt.seq == 7
    assert pkt.altitude_m == 1234.5
    assert pkt.velocity_mps == 67.25
    assert pkt.heading_deg == 359.0
    assert pkt.status == 0x0001


def test_reject_bad_length() -> None:
    try:
        decode_packet(b"too-short")
    except DecodeError:
        return
    raise AssertionError("expected DecodeError for short datagram")


def test_reject_bad_sync() -> None:
    raw = bytearray(build_packet(1, 0, 0.0, 0.0, 0.0))
    struct.pack_into(">H", raw, 0, 0x0000)
    # fix checksum over the mutated header so only sync fails
    checksum = zlib.crc32(bytes(raw[:28])) & 0xFFFFFFFF
    struct.pack_into(">I", raw, 28, checksum)
    try:
        decode_packet(bytes(raw))
    except DecodeError as exc:
        assert "sync" in str(exc).lower()
        return
    raise AssertionError("expected DecodeError for bad sync")


def test_reject_bad_checksum() -> None:
    raw = bytearray(build_packet(1, 0, 0.0, 0.0, 0.0))
    struct.pack_into(">I", raw, 28, 0xDEADBEEF)
    try:
        decode_packet(bytes(raw))
    except DecodeError as exc:
        assert "checksum" in str(exc).lower()
        return
    raise AssertionError("expected DecodeError for bad checksum")


def test_drop_tracker() -> None:
    t = DropTracker()
    assert t.observe(0) == 0
    assert t.observe(1) == 0
    assert t.observe(4) == 2
    assert t.dropped == 2
    assert t.received == 3


if __name__ == "__main__":
    test_round_trip()
    test_reject_bad_length()
    test_reject_bad_sync()
    test_reject_bad_checksum()
    test_drop_tracker()
    print("all decoder self-tests passed")
