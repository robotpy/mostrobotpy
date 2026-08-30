project('robotpy-tunables', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++23',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

tunables_sources += files(
    'tunables/src/main.cpp',
    'tunables/src/TunablePython.cpp',
    'tunables/src/rpy/MockTunableBackendFunctions.cpp',
    'tunables/src/rpy/PyComplexTunableAdapter.cpp',
    'tunables/src/rpy/PyMutationList.cpp',
    'tunables/src/rpy/PyTunable.cpp',
    'tunables/src/rpy/PyTunableTable.cpp',
    'tunables/src/rpy/TunableStorage.cpp',
    'tunables/src/rpy/TunableValuePython.cpp',
)

subdir('semiwrap/modules')
