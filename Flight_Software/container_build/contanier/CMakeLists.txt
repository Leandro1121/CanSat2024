# Add any internal function script here
set (SOURCES
        container_build.c
        c_files/helper_funcs.c
        )
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
target_link_libraries(container_build hardware_adc)
target_link_libraries(container_build pico_multicore)

if (PICO_CYW43_SUPPORTED)
    target_link_libraries(container_build
        pico_cyw43_arch_none
    )
endif()
# Enable extra outputs, such as disassembly
pico_enable_stdio_uart(container_build 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(container_build)

# add url via pico_set_program_url
example_auto_set_url(container_build)

