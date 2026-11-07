# telemetry-link (Milestone 1)

Fixed 32-byte UDP telemetry: C++ sender + Python decoder.

Packet spec: see the [Telemetry M1 packet spec](https://cursor.com/canvas/store-b7bfc342-557d-410e-99da-cfdc6897d983/92d0a87f-8bc9-4b8f-9f6a-7d61f52a661b) Page.

## Decoder

```bash
cd decoder
python3 test_decode.py
python3 main.py --port 5005
```

## Sender (C++)

```bash
cd sender
make          # or: cmake -B build && cmake --build build
./sender --once                    # one hardcoded packet
./sender --count 20 --rate 10      # short simulation burst
```

## Demo (both)

```bash
./scripts/run_demo.sh
```

Default listen/send port is 5005. Multi-byte fields are network byte order (big-endian).

## Drop tracking (wire-level gap demo)

The decoder counts `seq` gaps. When a gap appears it prints `skipped=N` on that line, and the exit summary includes `dropped=`.

Happy path (no gaps): `./scripts/run_demo.sh` should end with `dropped=0`.

Forced gap (no real packet loss needed):

```bash
# terminal 1
cd decoder && python3 main.py --port 5005 --max-packets 5

# terminal 2
cd decoder && python3 - <<'PY'
from decode import build_packet
import socket, time
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for seq in (0, 1, 2, 5, 6):  # jump 2 -> 5 skips 3 and 4
    s.sendto(build_packet(seq, seq * 100, 100.0, 10.0, 90.0), ("127.0.0.1", 5005))
    time.sleep(0.05)
s.close()
PY
```

Expect `skipped=2` when `seq=5` arrives, then `summary: ... dropped=2`.

## Still optional for M1 (target Nov 8)

1. Publish this folder as a public GitHub repo under `kdll99` (not created yet) so the Nov 15 resume checkpoint can link it
