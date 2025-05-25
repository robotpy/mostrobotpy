project('robotpy-cscore', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

cscore_sources += files(
  'cscore/src/main.cpp',
  'cscore/cvnp/cvnp.cpp',
  'cscore/cvnp/cvnp_synonyms.cpp',
)

#
# Statically link to cscore/opencv to avoid exporting opencv symbols
#

cpp = meson.get_compiler('cpp')
libs_path = meson.current_source_dir() + '/lib/lib'

cscore_deps += [
    cpp.find_library('opencv4100', dirs: libs_path),
    cpp.find_library('cscore', dirs: libs_path),
    cpp.find_library('cameraserver', dirs: libs_path),
]

subdir('semiwrap/modules')
