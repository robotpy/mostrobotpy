project('wpiutil-test', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

py = import('python').find_installation()

subdir('semiwrap')

py.extension_module(
  'module',
  sources: files(
    'wpiutil_test/module.cpp',
    'wpiutil_test/sendable_test.cpp',
    'wpiutil_test/struct_test.cpp',
  ),
  install: true,
  subdir: 'wpiutil_test',
  dependencies: [dependency('semiwrap'), dependency('wpiutil'), dependency('nanobind')],
)
