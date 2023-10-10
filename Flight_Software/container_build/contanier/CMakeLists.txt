# Add any internal function script here
set (SOURCES
        container_build.c
        bmp280_i2c.c)
# For .h files        
include_directories(${CMAKE_SOURCE_DIR})

add_executable(container_build
        ${SOURCES}
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(container_build pico_stdlib)
target_link_libraries(container_build hardware_i2c)
target_link_libraries(container_build hardware_uart)
target_link_libraries(container_build hardware_spi)

# create map/bin/hex file etc.
pico_add_extra_outputs(container_build)

# add url via pico_set_program_url
example_auto_set_url(container_build)

