CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
LDFLAGS ?= -lz

sender: main.cpp packet.hpp
	$(CXX) $(CXXFLAGS) -o $@ main.cpp $(LDFLAGS)

.PHONY: clean
clean:
	rm -f sender
