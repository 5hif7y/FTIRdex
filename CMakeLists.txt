cmake_minimum_required(VERSION 3.15)
project(FTIRdex LANGUAGES C)

# Set C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Add the libnativegui subdirectory
add_subdirectory(libnativegui)

# Add FTIRdex executable
add_executable(FTIRdex FTIRdex/main.c)

# Include directories
target_include_directories(FTIRdex PRIVATE libnativegui FTIRdex)

# Windows resource files and subsystem configuration
if(WIN32)
    target_sources(FTIRdex PRIVATE FTIRdex/resource.rc)
    set_target_properties(FTIRdex PROPERTIES WIN32_EXECUTABLE TRUE)
endif()

# Link with nativegui static library target
target_link_libraries(FTIRdex PRIVATE nativegui)

# Copy the Python scripts and resource folder to the output directory on build
# This ensures all dependencies are local to the executable
add_custom_command(TARGET FTIRdex POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/FTIRdex/process_ftir.py" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/FTIRdex/make_ico.py" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/icono.ico" "$<TARGET_FILE_DIR:FTIRdex>/"
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/FTIRlib" "$<TARGET_FILE_DIR:FTIRdex>/FTIRlib"
    COMMENT "Copying Python assets and library folders to build folder"
)
