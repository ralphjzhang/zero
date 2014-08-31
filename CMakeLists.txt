cmake_minimum_required(VERSION 2.8)

project(zero)

set(ANACONDA_HOME $ENV{HOME}/anaconda)
set(ZERO_HOME ${CMAKE_SOURCE_DIR})


if("${CMAKE_SYSTEM}" MATCHES "Linux")
    message("Using Linux build")

    set(CMAKE_C_COMPILER "${ANACONDA_HOME}/bin/clang")
    set(CMAKE_CXX_COMPILER "${ANACONDA_HOME}/bin/clang++")

endif("${CMAKE_SYSTEM}" MATCHES "Linux")

include_directories(
    ${ANACONDA_HOME}/include
    ${ZERO_HOME}/include
    )

link_directories(
    ${ANACONDA_HOME}/lib
    ${ZERO_HOME}/lib
    )

add_subdirectory(
    zerocpp
    )

