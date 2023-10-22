# Add any internal function script here
set (SOURCES
        container_build.c
        c_files/bmp280_i2c.c
        c_files/bno055.c
        c_files/bno055_support.c
        c_files/helper_funcs.c
        )
# For .h files        
include_directories(${CMAKE_SOURCE_DIR})

# # Add libraries
add_library(power_status_adc INTERFACE)

target_sources(power_status_adc INTERFACE
        ${CMAKE_CURRENT_LIST_DIR}/c_files/power_status.c
        )
target_include_directories(power_status_adc INTERFACE
        ${CMAKE_CURRENT_LIST_DIR}
        )

add_executable(container_build
        ${SOURCES}
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(container_build pico_stdlib)
target_link_libraries(container_build hardware_i2c)
target_link_libraries(container_build hardware_uart)
target_link_libraries(container_build hardware_spi)
target_link_libraries(container_build power_status_adc)
target_link_libraries(container_build pico_multicore)

target_link_libraries(power_status_adc INTERFACE
        hardware_adc
        hardware_gpio
        )

if (PICO_CYW43_SUPPORTED)
    target_link_libraries(container_build
        pico_cyw43_arch_none
    )
endif()
# create map/bin/hex file etc.
pico_add_extra_outputs(container_build)

# add url via pico_set_program_url
example_auto_set_url(container_build)

