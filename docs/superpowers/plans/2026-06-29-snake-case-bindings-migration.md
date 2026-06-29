# Snake Case Bindings Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert all mostrobotpy Python bindings, pure-Python code, tests, examples, snippets, and docs to snake_case APIs with CAPS_CASE enum values and no compatibility aliases.

**Architecture:** Add a reusable `libcst`-based migration tool under `devtools/snake_case_migration`, drive semiwrap-generated API names with `[tool.semiwrap].name_transform`, record all automated and manual decisions in `snake_case_migration.toml`, then migrate each subproject in dependency order with separate commits. Semiwrap transformer defects are fixed upstream in the editable semiwrap checkout at `/home/virtuald/src/frc/codex/semiwrap` by a dispatched subagent, not worked around in mostrobotpy.

**Tech Stack:** Python 3.11+, semiwrap editable install, `libcst`, `tomlkit`, pytest, `./rdev.sh`, hatch/meson build hooks.

## Global Constraints

- Configure all semiwrap-based mostrobotpy projects to transform generated binding names to snake_case.
- Configure enum values from generated bindings to CAPS_CASE.
- Convert pure-Python package code, tests, examples, snippets, docs, and internal project-local names to snake_case where practical.
- Keep class, type, and enum type names in PascalCase.
- Add no compatibility aliases for old camelCase names.
- Use semiwrap's `name_transform` acronym support where appropriate.
- If semiwrap bugs are encountered, dispatch a subagent to fix `/home/virtuald/src/frc/codex/semiwrap` immediately; do not use worktrees and do not work around the bug in mostrobotpy.
- Use one repo-wide migration branch with separate per-subproject commits.
- Prefer `./rdev.sh develop` for the full repo, `./rdev.sh develop robotpy-wpilib` for one project, and `./rdev.sh develop --stop-at robotpy-wpilib` for dependency-chain builds.
- Verify each subproject with its `tests/run_tests.py` when present.
- Do not touch the unrelated untracked `networktables.json` file.

---

## File Structure

Create:

- `devtools/snake_case_migration/__init__.py` — package marker and exported version.
- `devtools/snake_case_migration/__main__.py` — `python -m devtools.snake_case_migration` entry point.
- `devtools/snake_case_migration/cli.py` — argparse CLI wiring for manifest, pyproject, scan, rewrite, text, and audit commands.
- `devtools/snake_case_migration/names.py` — semiwrap-backed name conversion and acronym configuration.
- `devtools/snake_case_migration/manifest.py` — TOML manifest dataclasses, deterministic read/write, override handling.
- `devtools/snake_case_migration/scan_py.py` — Python AST/CST scanners that discover definitions and candidate references.
- `devtools/snake_case_migration/rewrite_py.py` — `libcst` transformer for definitions, attribute access, calls, imports, and keyword arguments.
- `devtools/snake_case_migration/rewrite_text.py` — conservative manifest-based rewriter for `.md`, `.rst`, and other text examples.
- `devtools/snake_case_migration/audit.py` — remaining camelCase/reference audit.
- `tests/devtools/test_snake_case_migration_names.py` — conversion tests.
- `tests/devtools/test_snake_case_migration_manifest.py` — manifest tests.
- `tests/devtools/test_snake_case_migration_rewrite_py.py` — CST rewrite tests.
- `tests/devtools/test_snake_case_migration_audit.py` — audit tests.
- `snake_case_migration.toml` — repo migration manifest and acronym list.

Modify:

- `rdev_requirements.txt` — add `libcst`.
- Semiwrap project TOML files:
  - `subprojects/pyntcore/pyproject.toml`
  - `subprojects/robotpy-apriltag/pyproject.toml`
  - `subprojects/robotpy-cscore/pyproject.toml`
  - `subprojects/robotpy-hal/pyproject.toml`
  - `subprojects/robotpy-halsim-gui/pyproject.toml`
  - `subprojects/robotpy-romi/pyproject.toml`
  - `subprojects/robotpy-wpilib/pyproject.toml`
  - `subprojects/robotpy-wpilog/pyproject.toml`
  - `subprojects/robotpy-wpimath/pyproject.toml`
  - `subprojects/robotpy-wpimath/tests/cpp/pyproject.toml`
  - `subprojects/robotpy-wpinet/pyproject.toml`
  - `subprojects/robotpy-wpiutil/pyproject.toml`
  - `subprojects/robotpy-xrp/pyproject.toml`
- Subproject source/test files migrated per task.
- `examples/**/*.py`, `snippets/**/*.py`, and docs `.rst`/`.md` files migrated after package APIs stabilize.

---

### Task 1: Add migration tool dependency and package scaffold

**Files:**
- Modify: `rdev_requirements.txt`
- Create: `devtools/snake_case_migration/__init__.py`
- Create: `devtools/snake_case_migration/__main__.py`
- Create: `devtools/snake_case_migration/cli.py`
- Test: `tests/devtools/test_snake_case_migration_names.py`

**Interfaces:**
- Consumes: Existing `devtools` Python package.
- Produces: Runnable command `python -m devtools.snake_case_migration --help` and importable package `devtools.snake_case_migration`.

- [ ] **Step 1: Add failing scaffold tests**

Create `tests/devtools/test_snake_case_migration_names.py`:

```python
import subprocess
import sys


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "devtools.snake_case_migration", "--help"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert "snake_case_migration" in result.stdout
    assert "manifest" in result.stdout
    assert "rewrite-py" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_names.py::test_cli_help_runs -v
```

Expected: FAIL with `No module named devtools.snake_case_migration`.

- [ ] **Step 3: Add dependency and minimal CLI scaffold**

Append this line to `rdev_requirements.txt` if it is not already present:

```text
libcst
```

Create `devtools/snake_case_migration/__init__.py`:

```python
"""Reusable helpers for migrating semiwrap projects to snake_case APIs."""

__all__ = ["__version__"]
__version__ = "0.1.0"
```

Create `devtools/snake_case_migration/__main__.py`:

```python
from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `devtools/snake_case_migration/cli.py`:

```python
from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snake_case_migration",
        description="Migrate semiwrap-based Python projects to snake_case APIs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("manifest", help="Create or update manifest files")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    manifest_sub.add_parser("init", help="Create a new manifest")
    manifest_sub.add_parser("check", help="Validate an existing manifest")

    subparsers.add_parser("pyproject", help="Apply semiwrap name_transform settings")
    subparsers.add_parser("scan-py", help="Scan Python files and update mappings")
    subparsers.add_parser("rewrite-py", help="Rewrite Python files using mappings")
    subparsers.add_parser("rewrite-text", help="Rewrite docs/examples text using mappings")
    subparsers.add_parser("audit", help="Report remaining old-style names")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_names.py::test_cli_help_runs -v
```

Expected: PASS.

- [ ] **Step 5: Commit scaffold**

Run:

```bash
git add rdev_requirements.txt devtools/snake_case_migration tests/devtools/test_snake_case_migration_names.py
git commit -m "tools: scaffold snake case migration CLI"
```

---

### Task 2: Implement semiwrap-backed name conversion

**Files:**
- Modify: `devtools/snake_case_migration/names.py`
- Modify: `devtools/snake_case_migration/cli.py`
- Modify: `tests/devtools/test_snake_case_migration_names.py`

**Interfaces:**
- Consumes: `semiwrap.name_transform.resolve_name_transform`.
- Produces: `DEFAULT_ACRONYMS`, `to_snake_case(name: str, kind: NameKind = "method") -> str`, `to_caps_case(name: str) -> str`, and `is_probably_type_name(name: str) -> bool`.

- [ ] **Step 1: Write failing conversion tests**

Extend `tests/devtools/test_snake_case_migration_names.py`:

```python
from devtools.snake_case_migration.names import (
    DEFAULT_ACRONYMS,
    is_probably_type_name,
    to_caps_case,
    to_snake_case,
)


def test_snake_case_uses_wpilib_acronyms():
    assert "FPGA" in DEFAULT_ACRONYMS
    assert to_snake_case("GetFPGATime") == "get_fpga_time"
    assert to_snake_case("isDSAttached") == "is_ds_attached"
    assert to_snake_case("toJSON") == "to_json"
    assert to_snake_case("getI2CHandle") == "get_i2c_handle"


def test_caps_case_uses_wpilib_acronyms():
    assert to_caps_case("kHTTPServer") == "K_HTTP_SERVER"
    assert to_caps_case("valueOne") == "VALUE_ONE"


def test_type_name_detection_keeps_pascal_case_types():
    assert is_probably_type_name("TimedRobot") is True
    assert is_probably_type_name("NetworkTableInstance") is True
    assert is_probably_type_name("getDefault") is False
    assert is_probably_type_name("robotInit") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_names.py -v
```

Expected: FAIL with `No module named devtools.snake_case_migration.names`.

- [ ] **Step 3: Implement name conversion**

Create `devtools/snake_case_migration/names.py`:

```python
from __future__ import annotations

from typing import Literal

from semiwrap.name_transform import resolve_name_transform

NameKind = Literal["function", "method", "attribute", "enum_value", "parameter"]

DEFAULT_ACRONYMS: tuple[str, ...] = (
    "mDNS",
    "DS",
    "CAN",
    "PWM",
    "I2C",
    "SPI",
    "NT",
    "JSON",
    "PID",
    "IMU",
    "HAL",
    "JNI",
    "USB",
    "HTTP",
    "URI",
    "URL",
    "CPU",
    "FPGA",
    "FMS",
    "PCM",
    "PDP",
    "PDH",
    "RIO",
)

_SNAKE_TRANSFORM = resolve_name_transform("snake_case", acronyms=DEFAULT_ACRONYMS)
_CAPS_TRANSFORM = resolve_name_transform("CAPS_CASE", acronyms=DEFAULT_ACRONYMS)


def is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def is_probably_type_name(name: str) -> bool:
    if not name or "_" in name or is_dunder(name):
        return False
    return name[0].isupper() and any(ch.islower() for ch in name[1:])


def to_snake_case(name: str, kind: NameKind = "method") -> str:
    if is_dunder(name):
        return name
    return _SNAKE_TRANSFORM(name, kind)


def to_caps_case(name: str) -> str:
    if is_dunder(name):
        return name
    return _CAPS_TRANSFORM(name, "enum_value")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_names.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit name conversion**

Run:

```bash
git add devtools/snake_case_migration/names.py tests/devtools/test_snake_case_migration_names.py
git commit -m "tools: add semiwrap-backed snake case conversion"
```

---

### Task 3: Implement deterministic TOML manifest support

**Files:**
- Create: `devtools/snake_case_migration/manifest.py`
- Modify: `devtools/snake_case_migration/cli.py`
- Create: `tests/devtools/test_snake_case_migration_manifest.py`
- Create: `snake_case_migration.toml`

**Interfaces:**
- Consumes: `DEFAULT_ACRONYMS` from Task 2.
- Produces: `Manifest`, `Mapping`, `Ignore`, `load_manifest(path)`, `save_manifest(path, manifest)`, `merge_mapping(manifest, mapping)`, CLI commands `manifest init` and `manifest check`.

- [ ] **Step 1: Write failing manifest tests**

Create `tests/devtools/test_snake_case_migration_manifest.py`:

```python
from pathlib import Path

from devtools.snake_case_migration.manifest import (
    Ignore,
    Manifest,
    Mapping,
    load_manifest,
    merge_mapping,
    save_manifest,
)


def test_manifest_round_trip_is_deterministic(tmp_path: Path):
    path = tmp_path / "snake_case_migration.toml"
    manifest = Manifest(
        acronyms=["DS", "FPGA"],
        mappings=[
            Mapping(kind="method", old="GetFPGATime", new="get_fpga_time", source="test"),
            Mapping(kind="enum_value", old="kValueOne", new="K_VALUE_ONE", source="test"),
        ],
        ignored=[Ignore(name="__iter__", reason="dunder protocol")],
    )
    save_manifest(path, manifest)
    first = path.read_text()
    loaded = load_manifest(path)
    save_manifest(path, loaded)
    assert path.read_text() == first
    assert loaded.mappings[0].old == "GetFPGATime"


def test_merge_mapping_preserves_manual_override():
    manifest = Manifest(
        mappings=[
            Mapping(
                kind="method",
                old="ConfigPythonLogging",
                new="configure_python_logging",
                source="manual",
                reason="clearer public API",
            )
        ]
    )
    merge_mapping(
        manifest,
        Mapping(kind="method", old="ConfigPythonLogging", new="config_python_logging", source="generated"),
    )
    assert manifest.mappings[0].new == "configure_python_logging"
    assert manifest.mappings[0].source == "manual"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_manifest.py -v
```

Expected: FAIL with `No module named devtools.snake_case_migration.manifest`.

- [ ] **Step 3: Implement manifest module**

Create `devtools/snake_case_migration/manifest.py`:

```python
from __future__ import annotations

import dataclasses
from pathlib import Path

import tomlkit

from .names import DEFAULT_ACRONYMS


@dataclasses.dataclass(slots=True)
class Mapping:
    kind: str
    old: str
    new: str
    source: str
    scope: str = "global"
    reason: str = ""


@dataclasses.dataclass(slots=True)
class Ignore:
    name: str
    reason: str
    scope: str = "global"


@dataclasses.dataclass(slots=True)
class Manifest:
    acronyms: list[str] = dataclasses.field(default_factory=lambda: list(DEFAULT_ACRONYMS))
    mappings: list[Mapping] = dataclasses.field(default_factory=list)
    ignored: list[Ignore] = dataclasses.field(default_factory=list)
    semiwrap_bugs: list[dict[str, str]] = dataclasses.field(default_factory=list)


def _mapping_key(mapping: Mapping) -> tuple[str, str, str]:
    return (mapping.scope, mapping.kind, mapping.old)


def merge_mapping(manifest: Manifest, mapping: Mapping) -> None:
    incoming_key = _mapping_key(mapping)
    for idx, existing in enumerate(manifest.mappings):
        if _mapping_key(existing) == incoming_key:
            if existing.source == "manual":
                return
            manifest.mappings[idx] = mapping
            return
    manifest.mappings.append(mapping)


def load_manifest(path: str | Path) -> Manifest:
    data = tomlkit.parse(Path(path).read_text())
    manifest = Manifest(acronyms=list(data.get("config", {}).get("acronyms", DEFAULT_ACRONYMS)))
    for item in data.get("mapping", []):
        manifest.mappings.append(Mapping(**dict(item)))
    for item in data.get("ignored", []):
        manifest.ignored.append(Ignore(**dict(item)))
    manifest.semiwrap_bugs = [dict(item) for item in data.get("semiwrap_bug", [])]
    return manifest


def save_manifest(path: str | Path, manifest: Manifest) -> None:
    doc = tomlkit.document()
    config = tomlkit.table()
    config.add("acronyms", sorted(dict.fromkeys(manifest.acronyms), key=str.casefold))
    doc.add("config", config)

    for mapping in sorted(manifest.mappings, key=_mapping_key):
        item = tomlkit.table()
        for field in ("scope", "kind", "old", "new", "source", "reason"):
            value = getattr(mapping, field)
            if value:
                item.add(field, value)
        doc.append("mapping", item)

    for ignored in sorted(manifest.ignored, key=lambda i: (i.scope, i.name)):
        item = tomlkit.table()
        item.add("scope", ignored.scope)
        item.add("name", ignored.name)
        item.add("reason", ignored.reason)
        doc.append("ignored", item)

    for bug in manifest.semiwrap_bugs:
        item = tomlkit.table()
        for key in sorted(bug):
            item.add(key, bug[key])
        doc.append("semiwrap_bug", item)

    Path(path).write_text(tomlkit.dumps(doc))
```

Update `devtools/snake_case_migration/cli.py` so `manifest init` and `manifest check` work:

```python
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .manifest import Manifest, load_manifest, save_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snake_case_migration",
        description="Migrate semiwrap-based Python projects to snake_case APIs.",
    )
    parser.add_argument("--manifest", default="snake_case_migration.toml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("manifest", help="Create or update manifest files")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    manifest_sub.add_parser("init", help="Create a new manifest")
    manifest_sub.add_parser("check", help="Validate an existing manifest")

    subparsers.add_parser("pyproject", help="Apply semiwrap name_transform settings")
    subparsers.add_parser("scan-py", help="Scan Python files and update mappings")
    subparsers.add_parser("rewrite-py", help="Rewrite Python files using mappings")
    subparsers.add_parser("rewrite-text", help="Rewrite docs/examples text using mappings")
    subparsers.add_parser("audit", help="Report remaining old-style names")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)

    if args.command == "manifest" and args.manifest_command == "init":
        if manifest_path.exists():
            load_manifest(manifest_path)
        else:
            save_manifest(manifest_path, Manifest())
        return 0

    if args.command == "manifest" and args.manifest_command == "check":
        load_manifest(manifest_path)
        return 0

    return 0
```

Create root `snake_case_migration.toml` by running:

```bash
python -m devtools.snake_case_migration --manifest snake_case_migration.toml manifest init
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_manifest.py tests/devtools/test_snake_case_migration_names.py -v
python -m devtools.snake_case_migration --manifest snake_case_migration.toml manifest check
```

Expected: PASS and exit code 0.

- [ ] **Step 5: Commit manifest support**

Run:

```bash
git add devtools/snake_case_migration/manifest.py devtools/snake_case_migration/cli.py tests/devtools/test_snake_case_migration_manifest.py snake_case_migration.toml
git commit -m "tools: add snake case migration manifest"
```

---

### Task 4: Implement Python CST rewriting and audit primitives

**Files:**
- Create: `devtools/snake_case_migration/rewrite_py.py`
- Create: `devtools/snake_case_migration/audit.py`
- Modify: `devtools/snake_case_migration/cli.py`
- Create: `tests/devtools/test_snake_case_migration_rewrite_py.py`
- Create: `tests/devtools/test_snake_case_migration_audit.py`

**Interfaces:**
- Consumes: `Manifest`, `Mapping`, and `load_manifest` from Task 3.
- Produces: `rewrite_python_source(source: str, manifest: Manifest) -> str` and `audit_python_source(source: str, manifest: Manifest) -> list[str]`.

- [ ] **Step 1: Write failing rewrite tests**

Create `tests/devtools/test_snake_case_migration_rewrite_py.py`:

```python
from devtools.snake_case_migration.manifest import Manifest, Mapping
from devtools.snake_case_migration.rewrite_py import rewrite_python_source


def test_rewrite_definitions_calls_attrs_and_keywords():
    manifest = Manifest(
        mappings=[
            Mapping(kind="method", old="robotInit", new="robot_init", source="test"),
            Mapping(kind="method", old="getDefault", new="get_default", source="test"),
            Mapping(kind="method", old="setExpiration", new="set_expiration", source="test"),
            Mapping(kind="parameter", old="initialPose", new="initial_pose", source="test"),
        ]
    )
    source = '''\
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        inst = wpilib.DriverStation.getDefault()
        self.drive.setExpiration(timeout=0.1)
        self.odometry.resetPosition(initialPose=self.pose)
'''
    assert rewrite_python_source(source, manifest) == '''\
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robot_init(self):
        inst = wpilib.DriverStation.get_default()
        self.drive.set_expiration(timeout=0.1)
        self.odometry.resetPosition(initial_pose=self.pose)
'''


def test_rewrite_preserves_type_names_and_dunders():
    manifest = Manifest(
        mappings=[
            Mapping(kind="function", old="makeCommand", new="make_command", source="test"),
            Mapping(kind="method", old="__iter__", new="__iter__", source="test"),
        ]
    )
    source = '''\
class MyCommand:
    def __iter__(self):
        return iter(())

def makeCommand():
    return MyCommand()
'''
    assert rewrite_python_source(source, manifest) == '''\
class MyCommand:
    def __iter__(self):
        return iter(())

def make_command():
    return MyCommand()
'''
```

Create `tests/devtools/test_snake_case_migration_audit.py`:

```python
from devtools.snake_case_migration.manifest import Manifest
from devtools.snake_case_migration.audit import audit_python_source


def test_audit_reports_camel_case_defs_and_attrs():
    messages = audit_python_source(
        "def robotInit():\n    wpilib.Timer.getFPGATimestamp()\n",
        Manifest(),
    )
    assert any("robotInit" in message for message in messages)
    assert any("getFPGATimestamp" in message for message in messages)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_rewrite_py.py tests/devtools/test_snake_case_migration_audit.py -v
```

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement rewrite and audit modules**

Create `devtools/snake_case_migration/rewrite_py.py`:

```python
from __future__ import annotations

import libcst as cst

from .manifest import Manifest


class _RenameTransformer(cst.CSTTransformer):
    def __init__(self, manifest: Manifest):
        self.name_map: dict[str, str] = {
            mapping.old: mapping.new
            for mapping in manifest.mappings
            if mapping.old != mapping.new
        }

    def _rename(self, value: str) -> str:
        return self.name_map.get(value, value)

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        return updated_node.with_changes(value=self._rename(updated_node.value))

    def leave_Attribute(
        self, original_node: cst.Attribute, updated_node: cst.Attribute
    ) -> cst.Attribute:
        return updated_node.with_changes(
            attr=updated_node.attr.with_changes(value=self._rename(updated_node.attr.value))
        )

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> cst.Param:
        return updated_node.with_changes(
            name=updated_node.name.with_changes(value=self._rename(updated_node.name.value))
        )

    def leave_Arg(self, original_node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
        if updated_node.keyword is None:
            return updated_node
        return updated_node.with_changes(
            keyword=updated_node.keyword.with_changes(
                value=self._rename(updated_node.keyword.value)
            )
        )


def rewrite_python_source(source: str, manifest: Manifest) -> str:
    module = cst.parse_module(source)
    return module.visit(_RenameTransformer(manifest)).code
```

Create `devtools/snake_case_migration/audit.py`:

```python
from __future__ import annotations

import re

import libcst as cst

from .manifest import Manifest
from .names import is_dunder, is_probably_type_name

_CAMEL_RE = re.compile(r"[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*")


class _AuditVisitor(cst.CSTVisitor):
    def __init__(self, manifest: Manifest):
        mapped = {mapping.old for mapping in manifest.mappings}
        ignored = {ignored.name for ignored in manifest.ignored}
        self.allowed = mapped | ignored
        self.messages: list[str] = []

    def _check(self, name: str, context: str) -> None:
        if name in self.allowed or is_dunder(name) or is_probably_type_name(name):
            return
        if _CAMEL_RE.search(name):
            self.messages.append(f"{context}: remaining camelCase name {name!r}")

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._check(node.name.value, "function")

    def visit_Attribute(self, node: cst.Attribute) -> None:
        self._check(node.attr.value, "attribute")

    def visit_Arg(self, node: cst.Arg) -> None:
        if node.keyword is not None:
            self._check(node.keyword.value, "keyword")


def audit_python_source(source: str, manifest: Manifest) -> list[str]:
    visitor = _AuditVisitor(manifest)
    cst.parse_module(source).visit(visitor)
    return visitor.messages
```

Update `devtools/snake_case_migration/cli.py` to import the modules without circular imports and keep existing behavior. Full file should still expose the commands from Task 3.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_rewrite_py.py tests/devtools/test_snake_case_migration_audit.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit rewrite primitives**

Run:

```bash
git add devtools/snake_case_migration/rewrite_py.py devtools/snake_case_migration/audit.py devtools/snake_case_migration/cli.py tests/devtools/test_snake_case_migration_rewrite_py.py tests/devtools/test_snake_case_migration_audit.py
git commit -m "tools: add Python rewrite and audit primitives"
```

---

### Task 5: Add file-based CLI commands for pyproject, scan, rewrite, text rewrite, and audit

**Files:**
- Create: `devtools/snake_case_migration/scan_py.py`
- Create: `devtools/snake_case_migration/rewrite_text.py`
- Modify: `devtools/snake_case_migration/cli.py`
- Modify: `devtools/snake_case_migration/rewrite_py.py`
- Modify: `devtools/snake_case_migration/audit.py`
- Modify: `tests/devtools/test_snake_case_migration_manifest.py`
- Modify: `tests/devtools/test_snake_case_migration_rewrite_py.py`

**Interfaces:**
- Consumes: Tasks 2-4.
- Produces exact commands used by later tasks:
  - `python -m devtools.snake_case_migration pyproject --write subprojects/pyntcore/pyproject.toml`
  - `python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-wpilib`
  - `python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-wpilib`
  - `python -m devtools.snake_case_migration rewrite-text --write docs README.md`
  - `python -m devtools.snake_case_migration audit subprojects/robotpy-wpilib`

- [ ] **Step 1: Write CLI integration tests**

Add this test to `tests/devtools/test_snake_case_migration_manifest.py`:

```python
import subprocess
import sys


def test_manifest_init_cli_writes_manifest(tmp_path):
    path = tmp_path / "manifest.toml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            str(path),
            "manifest",
            "init",
        ],
        check=True,
    )
    assert "[config]" in path.read_text()
```

Add this test to `tests/devtools/test_snake_case_migration_rewrite_py.py`:

```python
import subprocess
import sys
from pathlib import Path

from devtools.snake_case_migration.manifest import Manifest, Mapping, save_manifest


def test_rewrite_py_cli_rewrites_file(tmp_path: Path):
    manifest_path = tmp_path / "manifest.toml"
    source_path = tmp_path / "robot.py"
    save_manifest(
        manifest_path,
        Manifest(mappings=[Mapping(kind="method", old="robotInit", new="robot_init", source="test")]),
    )
    source_path.write_text("def robotInit():\n    pass\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            str(manifest_path),
            "rewrite-py",
            "--write",
            str(source_path),
        ],
        check=True,
    )
    assert source_path.read_text() == "def robot_init():\n    pass\n"
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
python -m pytest tests/devtools/test_snake_case_migration_manifest.py::test_manifest_init_cli_writes_manifest tests/devtools/test_snake_case_migration_rewrite_py.py::test_rewrite_py_cli_rewrites_file -v
```

Expected: `test_rewrite_py_cli_rewrites_file` FAILS because file rewriting is not implemented in the CLI.

- [ ] **Step 3: Implement file walking, pyproject application, and command handlers**

Create `devtools/snake_case_migration/scan_py.py`:

```python
from __future__ import annotations

import ast
from pathlib import Path

from .manifest import Manifest, Mapping, merge_mapping
from .names import is_dunder, is_probably_type_name, to_snake_case


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in path.rglob("*.py")
                if "__pycache__" not in p.parts and ".git" not in p.parts
            )
    return sorted(files)


def scan_python_file(path: Path, manifest: Manifest, scope: str) -> None:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if not is_dunder(name) and not is_probably_type_name(name):
                new = to_snake_case(name, "method")
                if new != name:
                    merge_mapping(
                        manifest,
                        Mapping(kind="method", old=name, new=new, source="scan-py", scope=scope),
                    )
        elif isinstance(node, ast.arg):
            name = node.arg
            if not is_dunder(name) and not is_probably_type_name(name):
                new = to_snake_case(name, "parameter")
                if new != name:
                    merge_mapping(
                        manifest,
                        Mapping(kind="parameter", old=name, new=new, source="scan-py", scope=scope),
                    )
```

Create `devtools/snake_case_migration/rewrite_text.py`:

```python
from __future__ import annotations

from pathlib import Path

from .manifest import Manifest

TEXT_SUFFIXES = {".md", ".rst", ".py", ".toml", ".yml", ".yaml"}


def iter_text_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in path.rglob("*")
                if p.is_file()
                and p.suffix in TEXT_SUFFIXES
                and "__pycache__" not in p.parts
                and ".git" not in p.parts
            )
    return sorted(files)


def rewrite_text_source(source: str, manifest: Manifest) -> str:
    result = source
    for mapping in sorted(manifest.mappings, key=lambda m: len(m.old), reverse=True):
        if mapping.old != mapping.new:
            result = result.replace(mapping.old, mapping.new)
    return result
```

Update `devtools/snake_case_migration/cli.py` to add shared path arguments, `--write`, and implementations. The command dispatch should:

```python
# after parsing args and loading manifest_path where needed:
# - pyproject: use tomlkit to add name_transform.default, name_transform.enum_value, and name_transform.acronyms to each path passed.
# - scan-py: call iter_python_files() and scan_python_file(), then save_manifest().
# - rewrite-py: for each Python file, call rewrite_python_source(); write only when --write is passed, otherwise print changed file paths.
# - rewrite-text: for each text file, call rewrite_text_source(); write only when --write is passed, otherwise print changed file paths.
# - audit: run audit_python_source() for each Python file; print messages and return 1 if any messages are found.
```

Use this exact semiwrap config for every pyproject command:

```toml
name_transform.default = "snake_case"
name_transform.enum_value = "CAPS_CASE"
name_transform.acronyms = ["mDNS", "DS", "CAN", "PWM", "I2C", "SPI", "NT", "JSON", "PID", "IMU", "HAL", "JNI", "USB", "HTTP", "URI", "URL", "CPU", "FPGA", "FMS", "PCM", "PDP", "PDH", "RIO"]
```

- [ ] **Step 4: Run all migration tool tests**

Run:

```bash
python -m pytest tests/devtools -v
```

Expected: PASS.

- [ ] **Step 5: Commit full CLI**

Run:

```bash
git add devtools/snake_case_migration tests/devtools
git commit -m "tools: add file-based snake case migration commands"
```

---

### Task 6: Apply semiwrap name_transform configuration

**Files:**
- Modify: all semiwrap-enabled pyproject files listed in File Structure.
- Modify: `snake_case_migration.toml` if the pyproject command records config metadata.

**Interfaces:**
- Consumes: `pyproject` CLI from Task 5.
- Produces: Every `[tool.semiwrap]` project has `name_transform.default`, `name_transform.enum_value`, and `name_transform.acronyms`.

- [ ] **Step 1: Run pyproject config command in dry-run mode**

Run:

```bash
python -m devtools.snake_case_migration pyproject \
  subprojects/pyntcore/pyproject.toml \
  subprojects/robotpy-apriltag/pyproject.toml \
  subprojects/robotpy-cscore/pyproject.toml \
  subprojects/robotpy-hal/pyproject.toml \
  subprojects/robotpy-halsim-gui/pyproject.toml \
  subprojects/robotpy-romi/pyproject.toml \
  subprojects/robotpy-wpilib/pyproject.toml \
  subprojects/robotpy-wpilog/pyproject.toml \
  subprojects/robotpy-wpimath/pyproject.toml \
  subprojects/robotpy-wpimath/tests/cpp/pyproject.toml \
  subprojects/robotpy-wpinet/pyproject.toml \
  subprojects/robotpy-wpiutil/pyproject.toml \
  subprojects/robotpy-xrp/pyproject.toml
```

Expected: command prints the 13 files that would change and exits 0.

- [ ] **Step 2: Apply pyproject config**

Run the same command with `--write`:

```bash
python -m devtools.snake_case_migration pyproject --write \
  subprojects/pyntcore/pyproject.toml \
  subprojects/robotpy-apriltag/pyproject.toml \
  subprojects/robotpy-cscore/pyproject.toml \
  subprojects/robotpy-hal/pyproject.toml \
  subprojects/robotpy-halsim-gui/pyproject.toml \
  subprojects/robotpy-romi/pyproject.toml \
  subprojects/robotpy-wpilib/pyproject.toml \
  subprojects/robotpy-wpilog/pyproject.toml \
  subprojects/robotpy-wpimath/pyproject.toml \
  subprojects/robotpy-wpimath/tests/cpp/pyproject.toml \
  subprojects/robotpy-wpinet/pyproject.toml \
  subprojects/robotpy-wpiutil/pyproject.toml \
  subprojects/robotpy-xrp/pyproject.toml
```

- [ ] **Step 3: Verify all config exists**

Run:

```bash
python - <<'PY'
from pathlib import Path
paths = [
    'subprojects/pyntcore/pyproject.toml',
    'subprojects/robotpy-apriltag/pyproject.toml',
    'subprojects/robotpy-cscore/pyproject.toml',
    'subprojects/robotpy-hal/pyproject.toml',
    'subprojects/robotpy-halsim-gui/pyproject.toml',
    'subprojects/robotpy-romi/pyproject.toml',
    'subprojects/robotpy-wpilib/pyproject.toml',
    'subprojects/robotpy-wpilog/pyproject.toml',
    'subprojects/robotpy-wpimath/pyproject.toml',
    'subprojects/robotpy-wpimath/tests/cpp/pyproject.toml',
    'subprojects/robotpy-wpinet/pyproject.toml',
    'subprojects/robotpy-wpiutil/pyproject.toml',
    'subprojects/robotpy-xrp/pyproject.toml',
]
for path in paths:
    text = Path(path).read_text()
    assert 'name_transform.default = "snake_case"' in text, path
    assert 'name_transform.enum_value = "CAPS_CASE"' in text, path
    assert 'name_transform.acronyms' in text, path
print('verified', len(paths), 'semiwrap pyprojects')
PY
```

Expected: `verified 13 semiwrap pyprojects`.

- [ ] **Step 4: Smoke-build first dependency project**

Run:

```bash
./rdev.sh develop robotpy-wpiutil
```

Expected: build succeeds. If the failure shows bad semiwrap name transformation, dispatch a semiwrap subagent with this exact instruction:

```text
Fix the semiwrap name_transform bug exposed by mostrobotpy's snake_case migration. Work in /home/virtuald/src/frc/codex/semiwrap, do not create a worktree, add or update semiwrap tests, and report the commit/hash or exact diff. After fixing, run the relevant semiwrap tests and tell me which mostrobotpy build command to rerun.
```

- [ ] **Step 5: Commit semiwrap config**

Run:

```bash
git add subprojects/*/pyproject.toml subprojects/robotpy-wpimath/tests/cpp/pyproject.toml snake_case_migration.toml
git commit -m "build: enable snake case semiwrap name transforms"
```

---

### Task 7: Migrate foundational semiwrap packages in dependency order

**Files:**
- Modify per package: package source, tests, semiwrap YAML overrides, generated import files, and `snake_case_migration.toml`.
- Packages in this task: `robotpy-wpiutil`, `robotpy-wpinet`, `robotpy-wpilog`, `robotpy-wpimath`, `robotpy-hal`, `pyntcore`.

**Interfaces:**
- Consumes: semiwrap config from Task 6 and rewrite tool from Task 5.
- Produces: six per-subproject commits with passing tests.

For each package below, run the exact package block. If a command fails because semiwrap transformed a name incorrectly, use the semiwrap subagent instruction from Task 6 before continuing.

- [ ] **Step 1: Migrate `robotpy-wpiutil`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-wpiutil
./rdev.sh develop --stop-at robotpy-wpiutil
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-wpiutil
python -m devtools.snake_case_migration audit subprojects/robotpy-wpiutil || true
python subprojects/robotpy-wpiutil/tests/run_tests.py
git add subprojects/robotpy-wpiutil snake_case_migration.toml
git commit -m "refactor: migrate robotpy-wpiutil to snake case"
```

Expected: tests pass. Every audit message is either fixed in source or recorded in `snake_case_migration.toml` as `[[ignored]]` with a concrete reason.

- [ ] **Step 2: Migrate `robotpy-wpinet`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-wpinet
./rdev.sh develop --stop-at robotpy-wpinet
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-wpinet
python -m devtools.snake_case_migration audit subprojects/robotpy-wpinet || true
python subprojects/robotpy-wpinet/tests/run_tests.py
git add subprojects/robotpy-wpinet snake_case_migration.toml
git commit -m "refactor: migrate robotpy-wpinet to snake case"
```

Expected: tests pass. Fix or record every audit message.

- [ ] **Step 3: Migrate `robotpy-wpilog`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-wpilog
./rdev.sh develop --stop-at robotpy-wpilog
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-wpilog
python -m devtools.snake_case_migration audit subprojects/robotpy-wpilog || true
python subprojects/robotpy-wpilog/tests/run_tests.py
git add subprojects/robotpy-wpilog snake_case_migration.toml
git commit -m "refactor: migrate robotpy-wpilog to snake case"
```

Expected: tests pass. Pay special attention to datalog record methods used by `examples/datalog/printlog.py`; examples are rewritten in Task 11.

- [ ] **Step 4: Migrate `robotpy-wpimath`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-wpimath
./rdev.sh develop --stop-at robotpy-wpimath
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-wpimath
python -m devtools.snake_case_migration audit subprojects/robotpy-wpimath || true
python subprojects/robotpy-wpimath/tests/run_tests.py
git add subprojects/robotpy-wpimath snake_case_migration.toml
git commit -m "refactor: migrate robotpy-wpimath to snake case"
```

Expected: tests pass. Pay special attention to constructor keyword arguments such as `initialPose`, `gyroAngle`, `frontLeft`, `frontRight`, `rearLeft`, `rearRight`, `minAcceleration`, and `maxAcceleration`; they must become snake_case unless recorded as external serialized names.

- [ ] **Step 5: Migrate `robotpy-hal`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-hal
./rdev.sh develop --stop-at robotpy-hal
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-hal
python -m devtools.snake_case_migration audit subprojects/robotpy-hal || true
python subprojects/robotpy-hal/tests/run_tests.py
git add subprojects/robotpy-hal snake_case_migration.toml
git commit -m "refactor: migrate robotpy-hal to snake case"
```

Expected: tests pass. HAL constants and externally specified C names must be reviewed before renaming; record intentional retained names.

- [ ] **Step 6: Migrate `pyntcore`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/pyntcore
./rdev.sh develop --stop-at pyntcore
python -m devtools.snake_case_migration rewrite-py --write subprojects/pyntcore
python -m devtools.snake_case_migration audit subprojects/pyntcore || true
python subprojects/pyntcore/tests/run_tests.py
git add subprojects/pyntcore snake_case_migration.toml
git commit -m "refactor: migrate pyntcore to snake case"
```

Expected: tests pass. Inline binding method `configPythonLogging` should become `config_python_logging` unless the manifest records a clearer manual override.

---

### Task 8: Migrate higher-level semiwrap packages

**Files:**
- Modify per package: package source, tests, semiwrap YAML overrides, generated import files, and `snake_case_migration.toml`.
- Packages in this task: `robotpy-apriltag`, `robotpy-cscore`, `robotpy-wpilib`, `robotpy-romi`, `robotpy-xrp`, `robotpy-halsim-gui`.

**Interfaces:**
- Consumes: foundational packages from Task 7.
- Produces: six per-subproject commits with passing tests.

- [ ] **Step 1: Migrate `robotpy-apriltag`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-apriltag
./rdev.sh develop --stop-at robotpy-apriltag
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-apriltag
python -m devtools.snake_case_migration audit subprojects/robotpy-apriltag || true
python subprojects/robotpy-apriltag/tests/run_tests.py
git add subprojects/robotpy-apriltag snake_case_migration.toml
git commit -m "refactor: migrate robotpy-apriltag to snake case"
```

Expected: tests pass.

- [ ] **Step 2: Migrate `robotpy-cscore`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-cscore
./rdev.sh develop --stop-at robotpy-cscore
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-cscore
python -m devtools.snake_case_migration audit subprojects/robotpy-cscore || true
python subprojects/robotpy-cscore/tests/run_tests.py
git add subprojects/robotpy-cscore snake_case_migration.toml
git commit -m "refactor: migrate robotpy-cscore to snake case"
```

Expected: tests pass. CameraServer and OpenCV helper names used by examples are rewritten in Task 11.

- [ ] **Step 3: Migrate `robotpy-wpilib`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-wpilib
./rdev.sh develop --stop-at robotpy-wpilib
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-wpilib
python -m devtools.snake_case_migration audit subprojects/robotpy-wpilib || true
python subprojects/robotpy-wpilib/tests/run_tests.py
git add subprojects/robotpy-wpilib snake_case_migration.toml
git commit -m "refactor: migrate robotpy-wpilib to snake case"
```

Expected: tests pass. Lifecycle hooks such as `robotInit`, `disabledPeriodic`, `teleopPeriodic`, `autonomousInit`, `testInit`, and `simulationPeriodic` must be migrated in framework dispatch and tests.

- [ ] **Step 4: Migrate `robotpy-romi`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-romi
./rdev.sh develop --stop-at robotpy-romi
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-romi
python -m devtools.snake_case_migration audit subprojects/robotpy-romi || true
python subprojects/robotpy-romi/tests/run_tests.py
git add subprojects/robotpy-romi snake_case_migration.toml
git commit -m "refactor: migrate robotpy-romi to snake case"
```

Expected: tests pass.

- [ ] **Step 5: Migrate `robotpy-xrp`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-xrp
./rdev.sh develop --stop-at robotpy-xrp
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-xrp
python -m devtools.snake_case_migration audit subprojects/robotpy-xrp || true
python subprojects/robotpy-xrp/tests/run_tests.py
git add subprojects/robotpy-xrp snake_case_migration.toml
git commit -m "refactor: migrate robotpy-xrp to snake case"
```

Expected: tests pass.

- [ ] **Step 6: Migrate `robotpy-halsim-gui`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-halsim-gui
./rdev.sh develop --stop-at robotpy-halsim-gui
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-halsim-gui
python -m devtools.snake_case_migration audit subprojects/robotpy-halsim-gui || true
python subprojects/robotpy-halsim-gui/tests/run_tests.py
git add subprojects/robotpy-halsim-gui snake_case_migration.toml
git commit -m "refactor: migrate robotpy-halsim-gui to snake case"
```

Expected: tests pass.

---

### Task 9: Migrate pure-Python and native-test packages

**Files:**
- Modify: `subprojects/robotpy-commands-v2/commands2/**/*.py`
- Modify: `subprojects/robotpy-commands-v2/tests/**/*.py`
- Modify: `subprojects/robotpy-halsim-ds-socket/**/*.py`
- Modify: `subprojects/robotpy-halsim-ws/**/*.py`
- Modify: `subprojects/robotpy-native-wpihal/tests/**/*.py`
- Modify: `snake_case_migration.toml`

**Interfaces:**
- Consumes: migrated `wpilib`, `wpimath`, `hal`, and `ntcore` packages.
- Produces: pure-Python APIs and tests using snake_case.

- [ ] **Step 1: Migrate `robotpy-commands-v2`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-commands-v2
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-commands-v2
python -m devtools.snake_case_migration audit subprojects/robotpy-commands-v2 || true
python subprojects/robotpy-commands-v2/tests/run_tests.py
git add subprojects/robotpy-commands-v2 snake_case_migration.toml
git commit -m "refactor: migrate commands2 to snake case"
```

Expected: tests pass. Review command lifecycle names and scheduler methods carefully; no camelCase compatibility aliases remain in `commands2`.

- [ ] **Step 2: Migrate `robotpy-halsim-ds-socket`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-halsim-ds-socket
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-halsim-ds-socket
python -m devtools.snake_case_migration audit subprojects/robotpy-halsim-ds-socket || true
python subprojects/robotpy-halsim-ds-socket/tests/run_tests.py
git add subprojects/robotpy-halsim-ds-socket snake_case_migration.toml
git commit -m "refactor: migrate halsim ds socket to snake case"
```

Expected: tests pass.

- [ ] **Step 3: Migrate `robotpy-halsim-ws`**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-halsim-ws
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-halsim-ws
python -m devtools.snake_case_migration audit subprojects/robotpy-halsim-ws || true
python subprojects/robotpy-halsim-ws/tests/run_tests.py
git add subprojects/robotpy-halsim-ws snake_case_migration.toml
git commit -m "refactor: migrate halsim ws to snake case"
```

Expected: tests pass. Preserve externally specified environment variable names such as `HALSIMWS_HOST` and `HALSIMWS_PORT`.

- [ ] **Step 4: Migrate `robotpy-native-wpihal` tests**

Run:

```bash
python -m devtools.snake_case_migration scan-py --write subprojects/robotpy-native-wpihal/tests
python -m devtools.snake_case_migration rewrite-py --write subprojects/robotpy-native-wpihal/tests
python -m devtools.snake_case_migration audit subprojects/robotpy-native-wpihal/tests || true
python subprojects/robotpy-native-wpihal/tests/run_tests.py
git add subprojects/robotpy-native-wpihal snake_case_migration.toml
git commit -m "refactor: migrate native wpihal tests to snake case"
```

Expected: tests pass.

---

### Task 10: Verify native-only packages and package import metadata

**Files:**
- Modify only if tests or import metadata fail:
  - `subprojects/robotpy-native-apriltag/pyproject.toml`
  - `subprojects/robotpy-native-datalog/pyproject.toml`
  - `subprojects/robotpy-native-ntcore/pyproject.toml`
  - `subprojects/robotpy-native-romi/pyproject.toml`
  - `subprojects/robotpy-native-wpilib/pyproject.toml`
  - `subprojects/robotpy-native-wpimath/pyproject.toml`
  - `subprojects/robotpy-native-wpinet/pyproject.toml`
  - `subprojects/robotpy-native-wpiutil/pyproject.toml`
  - `subprojects/robotpy-native-xrp/pyproject.toml`

**Interfaces:**
- Consumes: migrated dependent packages.
- Produces: confirmation that native-only projects do not need semiwrap name_transform settings.

- [ ] **Step 1: Verify native-only projects do not have accidental name_transform settings**

Run:

```bash
python - <<'PY'
from pathlib import Path
native = sorted(Path('subprojects').glob('robotpy-native-*/pyproject.toml'))
for path in native:
    text = path.read_text()
    assert 'name_transform.default' not in text, path
    assert '[tool.semiwrap]' not in text, path
print('verified native pyprojects:', len(native))
PY
```

Expected: prints `verified native pyprojects: 10`.

- [ ] **Step 2: Run native wpihal tests after dependent migration**

Run:

```bash
python subprojects/robotpy-native-wpihal/tests/run_tests.py
```

Expected: PASS.

- [ ] **Step 3: Commit only if files changed**

If no files changed, run:

```bash
git status --short
```

Expected: no native-only package changes. Do not create an empty commit.

If files changed because metadata had to be fixed, run:

```bash
git add subprojects/robotpy-native-* snake_case_migration.toml
git commit -m "refactor: update native package metadata for snake case migration"
```

---

### Task 11: Migrate examples, snippets, and docs

**Files:**
- Modify: `examples/**/*.py`
- Modify: `snippets/**/*.py`
- Modify: `docs/**/*.rst`
- Modify: `docs/**/*.md`
- Modify: `examples/CONTRIBUTING.md`
- Modify: `snake_case_migration.toml`

**Interfaces:**
- Consumes: stable package mappings from Tasks 7-9.
- Produces: examples, snippets, and docs that refer to snake_case APIs.

- [ ] **Step 1: Rewrite examples and snippets Python**

Run:

```bash
python -m devtools.snake_case_migration rewrite-py --write examples snippets
python -m devtools.snake_case_migration audit examples snippets || true
```

Expected: remaining audit messages are either user-defined type names or are fixed/recorded.

- [ ] **Step 2: Rewrite docs and markdown text**

Run:

```bash
python -m devtools.snake_case_migration rewrite-text --write docs examples/CONTRIBUTING.md README.md
```

Expected: command exits 0 and only replaces manifest-mapped names.

- [ ] **Step 3: Compile all examples and snippets**

Run:

```bash
python -m compileall -q examples snippets
```

Expected: exit code 0.

- [ ] **Step 4: Run example discovery smoke test**

Run:

```bash
./rdev.sh test-examples
```

Expected: PASS. If this command is too slow or requires unavailable hardware/simulator resources, run this fallback and record the reason in the commit message body:

```bash
python -m compileall -q examples snippets
```

- [ ] **Step 5: Commit examples/docs migration**

Run:

```bash
git add examples snippets docs README.md snake_case_migration.toml
git commit -m "docs: migrate examples and docs to snake case APIs"
```

---

### Task 12: Final repo-wide audit and verification

**Files:**
- Modify: `snake_case_migration.toml` for final ignored names and semiwrap bug records.
- Modify: any files found by audit.

**Interfaces:**
- Consumes: all prior migration tasks.
- Produces: final passing/audited repo state.

- [ ] **Step 1: Run migration tool tests**

Run:

```bash
python -m pytest tests/devtools -v
```

Expected: PASS.

- [ ] **Step 2: Run repo-wide audit**

Run:

```bash
python -m devtools.snake_case_migration audit subprojects examples snippets docs || true
```

Expected: audit output contains no unreviewed old camelCase API references. For every remaining message, either fix the reference or add an `[[ignored]]` entry to `snake_case_migration.toml` with a concrete reason.

- [ ] **Step 3: Run all subproject tests**

Run:

```bash
./rdev.sh test
```

Expected: PASS. If a test fails because a subproject was not rebuilt after a dependency rename, rerun the concrete build and test commands from the task that owns the failed subproject, then commit the fix with that subproject if source changes are needed.

- [ ] **Step 4: Run full editable build if practical**

Run:

```bash
./rdev.sh develop
```

Expected: PASS. If the build is too slow for the current session, run this minimum dependency-chain verification instead:

```bash
./rdev.sh develop --stop-at robotpy-wpilib
./rdev.sh develop robotpy-commands-v2
./rdev.sh develop robotpy-romi
./rdev.sh develop robotpy-xrp
```

- [ ] **Step 5: Commit final audit fixes**

Run:

```bash
git add subprojects examples snippets docs snake_case_migration.toml
git commit -m "refactor: finish snake case migration audit"
```

If `git diff --cached --quiet` exits 0, do not create an empty commit.

---

### Task 13: Final review handoff

**Files:**
- Read-only: changed files and git history.

**Interfaces:**
- Consumes: complete migration branch.
- Produces: review summary with verification evidence.

- [ ] **Step 1: Show commit structure**

Run:

```bash
git log --oneline --decorate -20
```

Expected: recent history shows the tool commits, semiwrap config commit, per-subproject migration commits, examples/docs commit, and final audit commit.

- [ ] **Step 2: Show clean status except known unrelated file**

Run:

```bash
git status --short
```

Expected: either clean status or only the pre-existing unrelated `?? networktables.json`.

- [ ] **Step 3: Prepare completion summary**

Collect these facts for the final response:

```bash
git rev-parse --short HEAD
python -m pytest tests/devtools -v
python -m devtools.snake_case_migration audit subprojects examples snippets docs || true
```

Expected: tool tests pass and audit has no unreviewed entries.
