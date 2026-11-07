// Telemetry M1 UDP sender: fixed 32-byte packets matching the packet spec.
#include "packet.hpp"

#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

namespace {

struct Options {
  std::string host = "127.0.0.1";
  int port = 5005;
  int count = 1;          // packets to send
  double rate_hz = 10.0;  // target send rate
  bool hardcode_only = false;
};

void usage(const char* argv0) {
  std::cerr
      << "Usage: " << argv0
      << " [--host H] [--port P] [--count N] [--rate HZ] [--once]\n"
      << "  Default: one packet to 127.0.0.1:5005.\n"
      << "  --once     force a single hardcoded packet (ignores --count/--rate).\n"
      << "  --count N  simulation loop packet count (default 1).\n"
      << "  --rate HZ  packets per second (default 10).\n";
}

bool parse_args(int argc, char** argv, Options* opt) {
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    auto need = [&](const char* name) -> const char* {
      if (i + 1 >= argc) {
        std::cerr << "missing value for " << name << "\n";
        return nullptr;
      }
      return argv[++i];
    };
    if (arg == "--host") {
      const char* v = need("--host");
      if (!v) return false;
      opt->host = v;
    } else if (arg == "--port") {
      const char* v = need("--port");
      if (!v) return false;
      opt->port = std::atoi(v);
    } else if (arg == "--count") {
      const char* v = need("--count");
      if (!v) return false;
      opt->count = std::atoi(v);
    } else if (arg == "--rate") {
      const char* v = need("--rate");
      if (!v) return false;
      opt->rate_hz = std::atof(v);
    } else if (arg == "--once") {
      opt->hardcode_only = true;
    } else if (arg == "--help" || arg == "-h") {
      usage(argv[0]);
      std::exit(0);
    } else {
      std::cerr << "unknown arg: " << arg << "\n";
      usage(argv[0]);
      return false;
    }
  }
  if (opt->hardcode_only) {
    opt->count = 1;
  }
  if (opt->count < 1 || opt->port <= 0 || opt->rate_hz <= 0.0) {
    std::cerr << "invalid --count/--port/--rate\n";
    return false;
  }
  return true;
}

uint64_t now_ms() {
  using namespace std::chrono;
  return duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count();
}

}  // namespace

int main(int argc, char** argv) {
  Options opt;
  if (!parse_args(argc, argv, &opt)) {
    return 2;
  }

  const int sock = ::socket(AF_INET, SOCK_DGRAM, 0);
  if (sock < 0) {
    std::perror("socket");
    return 1;
  }

  sockaddr_in addr{};
  addr.sin_family = AF_INET;
  addr.sin_port = htons(static_cast<uint16_t>(opt.port));
  if (::inet_pton(AF_INET, opt.host.c_str(), &addr.sin_addr) != 1) {
    std::cerr << "bad host: " << opt.host << "\n";
    ::close(sock);
    return 1;
  }

  const auto period = std::chrono::duration<double>(1.0 / opt.rate_hz);
  // Hardcoded baseline sample (Altitude / speed / heading) for the first packet.
  constexpr float kAlt0 = 1500.0f;
  constexpr float kVel0 = 55.0f;
  constexpr float kHdg0 = 270.0f;
  constexpr uint16_t kStatusOk = 0x0001;

  std::cout << "sending " << opt.count << " packet(s) to udp://" << opt.host << ":"
            << opt.port << " at " << opt.rate_hz << " Hz\n"
            << std::flush;

  for (int i = 0; i < opt.count; ++i) {
    const float altitude = kAlt0 + static_cast<float>(i) * 0.5f;
    const float velocity = kVel0;
    const float heading = kHdg0;
    const auto packet = telemetry::build_packet(
        static_cast<uint32_t>(i), now_ms(), altitude, velocity, heading, kStatusOk);

    const ssize_t n = ::sendto(sock, packet.data(), packet.size(), 0,
                               reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    if (n != static_cast<ssize_t>(packet.size())) {
      std::perror("sendto");
      ::close(sock);
      return 1;
    }

    if (i + 1 < opt.count) {
      std::this_thread::sleep_for(period);
    }
  }

  ::close(sock);
  std::cout << "done\n" << std::flush;
  return 0;
}
