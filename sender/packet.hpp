#pragma once

#include <array>
#include <cstdint>
#include <cstring>

#include <arpa/inet.h>
#include <zlib.h>

namespace telemetry {

constexpr std::size_t kPacketSize = 32;
constexpr std::size_t kHeaderBytes = 28;
constexpr uint16_t kSyncWord = 0xA55A;

inline uint64_t host_to_net64(uint64_t value) {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  return (static_cast<uint64_t>(htonl(static_cast<uint32_t>(value & 0xffffffffu))) << 32) |
         htonl(static_cast<uint32_t>(value >> 32));
#else
  return value;
#endif
}

inline uint32_t float_to_net(float value) {
  uint32_t bits = 0;
  static_assert(sizeof(float) == 4, "float must be 32-bit");
  std::memcpy(&bits, &value, sizeof(bits));
  return htonl(bits);
}

inline uint32_t crc32_header(const uint8_t* data) {
  return crc32(0L, data, static_cast<uInt>(kHeaderBytes)) & 0xffffffffu;
}

// Build one fixed 32-byte packet (big-endian), CRC32 over the first 28 bytes.
inline std::array<uint8_t, kPacketSize> build_packet(uint32_t seq,
                                                     uint64_t timestamp_ms,
                                                     float altitude_m,
                                                     float velocity_mps,
                                                     float heading_deg,
                                                     uint16_t status = 0) {
  std::array<uint8_t, kPacketSize> out{};
  uint8_t* p = out.data();

  const uint16_t sync_be = htons(kSyncWord);
  const uint32_t seq_be = htonl(seq);
  const uint64_t ts_be = host_to_net64(timestamp_ms);
  const uint32_t alt_be = float_to_net(altitude_m);
  const uint32_t vel_be = float_to_net(velocity_mps);
  const uint32_t hdg_be = float_to_net(heading_deg);
  const uint16_t status_be = htons(status);

  std::memcpy(p + 0, &sync_be, 2);
  std::memcpy(p + 2, &seq_be, 4);
  std::memcpy(p + 6, &ts_be, 8);
  std::memcpy(p + 14, &alt_be, 4);
  std::memcpy(p + 18, &vel_be, 4);
  std::memcpy(p + 22, &hdg_be, 4);
  std::memcpy(p + 26, &status_be, 2);

  const uint32_t checksum = crc32_header(out.data());
  const uint32_t checksum_be = htonl(checksum);
  std::memcpy(p + 28, &checksum_be, 4);
  return out;
}

}  // namespace telemetry
