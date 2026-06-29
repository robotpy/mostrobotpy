# Snake Case Bindings Migration Design

## Context

Mostrobotpy currently exposes Python APIs that largely mirror WPILib C++/Java-style names, including camelCase methods and mixed-case enum values. The project is intentionally making a breaking change: all mostrobotpy Python bindings and project-local Python code should move to Pythonic snake_case naming with no compatibility aliases.

Semiwrap is expected to provide automatic name transformation for wrapped C++ APIs. The local virtual environment already has an editable semiwrap install with this functionality. If the migration exposes semiwrap transformer bugs, those bugs should be fixed in semiwrap at `/home/virtuald/src/frc/codex/semiwrap` immediately by a dispatched subagent; mostrobotpy should not work around semiwrap defects.

## Goals

- Configure all semiwrap-based mostrobotpy projects to transform generated binding names to snake_case.
- Configure enum values from generated bindings to CAPS_CASE.
- Convert pure-Python package code, tests, examples, snippets, docs, and internal project-local names to snake_case where practical.
- Keep class, type, and enum type names in PascalCase.
- Add no compatibility aliases for old camelCase names.
- Automate the migration as much as possible with a reusable standalone refactoring/audit tool.
- Create an auditable migration manifest that records automated mappings, manual overrides, ignored names, and exception rationale.
- Commit the migration as one repo-wide branch with separate per-subproject commits.

## Non-goals

- Preserving backward compatibility for old names.
- Manually working around semiwrap name transformation bugs in mostrobotpy.
- Renaming public type/class names away from PascalCase.
- Rewriting serialized external data formats, protocol field names, vendor-defined strings, or user-facing literal values unless they refer to Python API names.
- Converting third-party APIs imported from outside mostrobotpy.

## Naming policy

The target naming policy is:

- Type, class, and enum type names stay `PascalCase`.
- Methods, functions, properties, keyword arguments, callback hooks, variables, and internal project-local names become `snake_case`.
- Enum values become `CAPS_CASE`.
- Python dunder/protocol methods stay unchanged.
- Old camelCase names are removed rather than preserved as aliases.

Lifecycle and framework hooks are part of the API migration. Examples include:

- `robotInit` -> `robot_init`
- `teleop_periodic` -> `teleop_periodic`
- `autonomous_init` -> `autonomous_init`
- `simulation_periodic` -> `simulation_periodic`

Acronym handling should use semiwrap's `name_transform` acronym map where semiwrap generates names. The reusable migration tool should use the same acronym map or an exported copy of it for pure-Python rewrites so names stay consistent across generated and manual code. Expected examples include:

- `getFPGATime` -> `get_fpga_time`
- `isDSAttached` -> `is_ds_attached`
- `toJSON` -> `to_json`
- `getI2CHandle` -> `get_i2c_handle`

Common RobotPy/WPILib acronyms to support include `DS`, `CAN`, `PWM`, `I2C`, `SPI`, `NT`, `JSON`, `PID`, `IMu`, `HAL`, `JNI`, `uSB`, `HTTP`, `uRI`, `uRL`, `CPu`, `FPGA`, `FMS`, `PCM`, `PDP`, `PDH`, `RIO`, and project-specific additions discovered during migration.

## Semiwrap configuration

Every project that has a `[tool.semiwrap]` section should gain the name transform settings:

```toml
[tool.semiwrap]
name_transform.default = "snake_case"
name_transform.enum_value = "CAPS_CASE"
```

The settings should be inserted without disrupting existing semiwrap settings such as `update_init`, `scan_headers_ignore`, exported type casters, or extension module declarations.

Projects without `[tool.semiwrap]`, such as native-only packages and pure-Python packages, should not receive this configuration unless they later adopt semiwrap.

## Reusable migration tool

Add a standalone migration/refactoring tool under `devtools/`. It should be usable on other semiwrap projects, not hard-coded solely to mostrobotpy.

The tool may use third-party dev dependencies installed into the virtualenv. `libcst` is the preferred foundation because it can rewrite Python while preserving formatting and comments.

### Core capabilities

The tool should provide these responsibilities:

1. **Name conversion library**
   - Convert non-type camelCase/Pascal-ish identifiers to snake_case.
   - Convert enum values to CAPS_CASE.
   - Preserve dunder names and explicitly ignored names.
   - use semiwrap's acronym map when possible, with local configuration for pure-Python-only terms.

2. **Manifest generation and maintenance**
   - Generate or update a readable manifest, preferably yAML or TOML.
   - Store mappings grouped by category: generated API, pure Python definitions, keyword arguments, attributes, enum values, manual overrides, and ignored names.
   - Preserve manual edits when regenerating.
   - Record the rationale for manual overrides and ignored names.

3. **Python source rewriting**
   - Rewrite function and method definitions.
   - Rewrite method calls and attribute access from manifest mappings.
   - Rewrite keyword arguments where the called API is migrated.
   - Rewrite imports and references when they point to renamed project-local functions or members.
   - Avoid rewriting external third-party API names unless explicitly mapped.
   - Support dry-run, diff, and write modes.

4. **Docs/examples text rewriting**
   - Apply conservative manifest-based substitutions to `.md`, `.rst`, examples, and snippets.
   - Avoid broad regex rewrites that alter non-API prose, external protocol names, or literal data.

5. **Audit/reporting**
   - Report remaining camelCase definitions and likely old API references.
   - Report mappings that were unused by the rewriter.
   - Report ambiguous names that require manual review.
   - Produce per-subproject reports suitable for review before each commit.

The tool should be tested before it is used for the migration.

## Migration manifest

The manifest is the audit trail and coordination point for the migration. It should capture:

- Automatically discovered semiwrap renames.
- Automatically inferred pure-Python renames.
- Manual API design overrides.
- Names intentionally ignored and why.
- Ambiguous mappings requiring review.
- Any semiwrap bugs discovered and their fix status.

The manifest should be deterministic enough that rerunning the generator does not produce noisy diffs. Manual overrides should take precedence over generated mappings.

## Manual exception policy

Automatic conversion is the default, but manual exceptions are expected. Exceptions should be recorded in the manifest.

use an exception when:

- The automatic name is technically correct but awkward or un-Pythonic.
- The C++ spelling contains redundant prefixes that should not be carried into Python.
- An enum value would otherwise become noisy, duplicated, or unclear.
- A name is externally specified and should not be changed.

Do not use a mostrobotpy exception to hide a semiwrap bug. If semiwrap produces an incorrect transformed name, dispatch a subagent to fix semiwrap at `/home/virtuald/src/frc/codex/semiwrap`, then rerun the affected mostrobotpy build or manifest generation.

## Execution strategy

The migration should happen on one repo-wide branch, but changes should be committed in reviewable units:

1. **Tooling commit**
   - Add the reusable migration tool.
   - Add tests for conversion, manifest handling, and representative CST rewrites.
   - Document required dev dependency installation.

2. **Semiwrap configuration commit**
   - Add `name_transform` settings to all semiwrap-enabled `pyproject.toml` files.
   - Build an initial wrapped project to verify the config is accepted.

3. **Per-subproject commits**
   - Migrate each subproject independently.
   - Generate/update manifest entries for that subproject.
   - Run the automated rewriter.
   - Manually resolve exceptions.
   - Run the subproject's `tests/run_tests.py` when present.
   - Commit source, tests, semiwrap yAML overrides, and manifest changes for that subproject together.

4. **Examples/snippets/docs commit**
   - Rewrite repo-level examples, snippets, and docs after the package APIs are stable.
   - Run syntax checks and selected smoke tests.

5. **Final audit commit**
   - Run repo-wide audit for remaining camelCase references.
   - Record intentionally retained names in the manifest.
   - Run as much of the full test/build matrix as practical.

## Build and test strategy

use the repository's existing development workflow:

- Prefer `./rdev.sh develop` for building the full repository.
- Prefer `./rdev.sh develop NAME` for rebuilding an individual project.
- use `./rdev.sh develop --stop-at NAME` when dependencies also need to be rebuilt.
- Each subproject with tests should be verified using its `tests/run_tests.py`.

The migration should use editable installs for Python projects where practical.

Validation gates:

- Migration tool tests pass before using the tool for source rewrites.
- Semiwrap config is accepted before bulk migration begins.
- Each migrated subproject's tests pass before its per-subproject commit.
- Build or test failures caused by semiwrap transformer defects trigger immediate semiwrap subagent work.
- Final audit finds no unreviewed camelCase API references.

## Error handling and semiwrap bug workflow

When a failure occurs, classify it before fixing:

1. **Semiwrap transformer bug**
   - Dispatch a subagent immediately to fix `/home/virtuald/src/frc/codex/semiwrap`.
   - Do not create a mostrobotpy workaround.
   - After the semiwrap fix, rerun the affected generation/build/test step.

2. **Migration tool bug**
   - Add a failing test to the migration tool.
   - Fix the tool.
   - Rerun the affected rewrite or audit.

3. **Manual API exception**
   - Record the override or ignore in the manifest.
   - Apply the local binding or pure-Python change.
   - Add or adjust tests that lock in the intended name.

4. **Test expectation failure**
   - update tests to the new snake_case API unless the failure reveals a real behavioral regression.

## Scope inventory

The current repository contains many independent migration surfaces:

- 12 semiwrap-enabled projects.
- About 305 semiwrap yAML files.
- About 176 subproject Python files.
- About 127 example/snippet Python files.
- `robotpy-commands-v2`, a large pure-Python package that will require substantial manual and automated renaming.
- Tests and documentation with thousands of old-style method and keyword references.

Because of this scope, the migration plan should avoid one giant undifferentiated commit. Per-subproject commits on a single branch provide a better review path while keeping the repository consistently headed toward the same breaking-change target.
