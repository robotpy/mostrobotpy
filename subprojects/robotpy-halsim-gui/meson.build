project('halsim-gui', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++23',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

halsim_gui_ext_sources += files(
    'halsim_gui/_ext/main.cpp',
)

subdir('semiwrap/modules')
