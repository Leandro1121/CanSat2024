add_executable(container_build
        container_build.c
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(container_build pico_stdlib)

# create map/bin/hex file etc.
pico_add_extra_outputs(container_build)

# add url via pico_set_program_url
example_auto_set_url(container_build)
