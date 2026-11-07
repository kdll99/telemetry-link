#!/usr/bin/env python3
"""UDP receiver for Telemetry M1 packets on the default port."""

from __future__ import annotations

import argparse
import socket
import sys

from decode import PACKET_SIZE, DecodeError, DropTracker, decode_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Listen for 32-byte telemetry UDP packets")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5005, help="UDP port (default 5005)")
    parser.add_argument(
        "--max-packets",
        type=int,
        default=0,
        help="stop after N good packets (0 = run forever)",
    )
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"listening on udp://{args.host}:{args.port}", flush=True)

    tracker = DropTracker()
    good = 0
    bad = 0

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            try:
                pkt = decode_packet(data)
            except DecodeError as exc:
                bad += 1
                print(f"reject from {addr[0]}:{addr[1]}: {exc}", flush=True)
                continue

            skipped = tracker.observe(pkt.seq)
            good += 1
            drop_note = f" skipped={skipped}" if skipped else ""
            print(
                f"seq={pkt.seq} t_ms={pkt.timestamp_ms} "
                f"alt={pkt.altitude_m:.2f}m vel={pkt.velocity_mps:.2f}m/s "
                f"hdg={pkt.heading_deg:.1f} status=0x{pkt.status:04X}"
                f"{drop_note}",
                flush=True,
            )

            if args.max_packets and good >= args.max_packets:
                break
    except KeyboardInterrupt:
        print("\nstopped by user", flush=True)
    finally:
        sock.close()

    print(
        f"summary: good={good} bad={bad} dropped={tracker.dropped}",
        flush=True,
    )
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
