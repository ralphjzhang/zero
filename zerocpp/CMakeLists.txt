
add_library(lib
    lib.cpp
    )

add_executable(test_lib
    lib_test.cpp
    )
target_link_libraries(test_lib
    lib
    gtest
    gtest_main
    )

