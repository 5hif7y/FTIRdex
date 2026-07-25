cmake_minimum_required(VERSION 3.15)

# Read version from centralized VERSION file
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" FTIRDEX_VERSION)
string(STRIP "${FTIRDEX_VERSION}" FTIRDEX_VERSION)

project(FTIRdex VERSION ${FTIRDEX_VERSION} LANGUAGES C)

# Set C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Add the libnativegui and libzipvfs subdirectories
add_subdirectory(libnativegui)
add_subdirectory(libzipvfs)

# Add FTIRdex executable
add_executable(FTIRdex
    FTIRdex/main.c
    FTIRdex/app_state.c
    FTIRdex/gui_render.c
)

# Include directories
target_include_directories(FTIRdex PRIVATE libnativegui FTIRdex libzipvfs/src)
target_compile_definitions(FTIRdex PRIVATE FTIRDEX_VERSION="${FTIRDEX_VERSION}")

# Windows resource files and subsystem configuration
if(WIN32)
    target_sources(FTIRdex PRIVATE FTIRdex/resource.rc)
    set_target_properties(FTIRdex PROPERTIES WIN32_EXECUTABLE TRUE)
endif()

# Link with nativegui and zipvfs static libraries
target_link_libraries(FTIRdex PRIVATE nativegui zipvfs)

# Copy the Python scripts and resource folder to the output directory on build
# This ensures all dependencies are local to the executable
add_custom_command(TARGET FTIRdex POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/FTIRdex/process_ftir.py" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/FTIRdex/make_ico.py" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/assets/icon.ico" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/assets/JetBrainsMono-Regular.ttf" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/FTIRlib" "$<TARGET_FILE_DIR:FTIRdex>/FTIRlib"
    COMMENT "Copying Python assets, fonts and library folders to build folder"
)

# Enable CTest suite 
enable_testing()
add_subdirectory(Tests/FTIRdex)

