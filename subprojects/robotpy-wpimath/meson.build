project('robotpy-wpimath', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

wpimath_sources += files(
    'wpimath/src/wpimath.cpp',
)

wpimath_controls_sources += files(
    'wpimath/_controls/controls.cpp',
)

wpimath_filter_sources += files(
    'wpimath/filter/filter.cpp',
)

wpimath_geometry_sources += files(
    'wpimath/geometry/geometry.cpp',
)

wpimath_interpolation_sources += files(
    'wpimath/interpolation/interpolation.cpp',
)

wpimath_kinematics_sources += files(
    'wpimath/kinematics/kinematics.cpp',
)

wpimath_spline_sources += files(
    'wpimath/spline/spline.cpp',
)

subdir('semiwrap/modules')
