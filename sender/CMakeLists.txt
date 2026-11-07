cmake_minimum_required(VERSION 3.16)
project(telemetry_sender LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ZLIB REQUIRED)

add_executable(sender main.cpp)
target_include_directories(sender PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(sender PRIVATE ZLIB::ZLIB)
