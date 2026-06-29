# Final Review Fix Report

Status: DONE

## Fixes Applied

- Renamed inline semiwrap pybind public names from camelCase to snake_case for:
  - `DCMotorSim` rotation/RPM helpers
  - `DifferentialDrivetrainSim` feet/inches/FPS helpers
  - `ElevatorSim` feet/inches/FPS helpers
  - `SingleJointedArmSim` degree/DPS helpers
  - `SimDeviceSim.enumerate_values` / `enumerate_devices`
  - `AddressableLED.set_data`
  - `Color8Bit.to_color`
  - `VideoMode.pixel_format`
  - `Tracer.get_epochs` (additional inline public-name hit found during YAML audit)
- Renamed `SysIdRoutineLog.MotorLog` overload outputs to `angular_position`, `angular_velocity`, and `angular_acceleration`.
- Extended `devtools.snake_case_migration audit` to scan `.pyi`, `.yml`, and `.yaml` files in addition to `.py`.
  - `.pyi` files use the existing CST audit path.
  - semiwrap YAML audit is scoped to public output strings: quoted `.def*()` names and `rename:` values.
- Added focused devtools tests for `.pyi` audit coverage and semiwrap YAML public binding names.
- Fixed `examples/wpinet/portfwd.py` argparse positional names to `remote_host` / `remote_port`.
- Updated leftover comment/doc references:
  - `snippets/robot/QuickVision/robot.py`: `robot_init()`
  - `commands2/waituntilcommand.py`: `wpilib.DriverStation.get_match_time`
- Fixed `pyntcore` inline `PubSubOptions` constructor public keyword names and docs after the expanded `.pyi` audit exposed those generated-stub names.

## Rebuilds

- `./rdev.sh develop robotpy-wpiutil` — passed
- `./rdev.sh develop robotpy-cscore` — passed
- `./rdev.sh develop --stop-at robotpy-wpilib` — passed
- `./rdev.sh develop pyntcore` — passed (needed for the audit-exposed `.pyi` keyword fixes)

## Tests and Verification

- `python subprojects/robotpy-wpiutil/tests/run_tests.py` — 79 passed
- `python subprojects/robotpy-cscore/tests/run_tests.py` — 3 passed
- `python subprojects/robotpy-wpilib/tests/run_tests.py` — 196 passed, 7 skipped, 1 xpassed
- `python subprojects/pyntcore/tests/run_tests.py` — 54 passed, 1 xpassed
- `python -m pytest tests/devtools -v` — 21 passed
- `python -m devtools.snake_case_migration audit subprojects examples snippets docs` — passed with no output
- `python -m compileall -q examples snippets` — passed
- Focused public-name proof scripts passed for:
  - public `.pyi` identifiers/parameters/attributes
  - semiwrap YAML `.def*()` names and `rename:` values
  - examples/snippets/docs text for the reviewed old names

## Notes

- Root untracked `networktables.json` was left untouched.
- Package tests created subproject-local untracked `networktables.json` artifacts; those generated test artifacts were removed.
- Raw text grep can still find C++ input identifiers such as `ResetData` in YAML keys and historical test fixtures in the migration plan; the focused proof intentionally excludes those because they are not public output names.
