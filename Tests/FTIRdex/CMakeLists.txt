cmake_minimum_required(VERSION 3.15)

project(FTIRdex_Tests C)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/unity
)

add_executable(test_ftirdex_core
    unity/unity.c
    test_ftirdex_core.c
)

add_test(NAME test_ftirdex_core COMMAND test_ftirdex_core)
