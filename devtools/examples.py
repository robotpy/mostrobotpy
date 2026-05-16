import dataclasses
import os
import pathlib
import subprocess
import sys
import typing as T

import click
import tomlkit

from .util import parse_input, run_cmd


def _validate_example_list(root: pathlib.Path, expected_dirs: T.Sequence[str]) -> None:
    expected = sorted(f"{name}/robot.py" for name in expected_dirs)
    actual = sorted(p.relative_to(root).as_posix() for p in root.rglob("robot.py"))

    if expected == actual:
        return

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    for path in missing:
        print(f"Missing: {path}")
    for path in extra:
        print(f"Extra: {path}")

    if not os.environ.get("FORCE_ANYWAYS"):
        print("ERROR: Not every robot.py file is in the list of tests!")
        sys.exit(1)


@dataclasses.dataclass
class ExamplesTests:
    base: T.List[str]
    ignored: T.List[str]


@dataclasses.dataclass
class ExamplesConfig:
    tests: ExamplesTests


def _load_tests_config(config_path: pathlib.Path) -> ExamplesConfig:
    try:
        data = tomlkit.parse(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise click.ClickException(f"Missing tests config: {config_path}")
    except Exception as exc:
        raise click.ClickException(f"Invalid tests config: {config_path}: {exc}")

    try:
        return parse_input(data, ExamplesConfig, config_path)
    except Exception as exc:
        raise click.ClickException(str(exc))


@click.command(name="test-examples")
@click.argument("test_name", required=False)
@click.option("-x", "--exitfirst", is_flag=True, help="Exit on first failed test.")
def test_examples(test_name: str | None, exitfirst: bool) -> None:
    """Run tests on robot examples."""
    root = pathlib.Path(__file__).parent.parent / "examples" / "robot"
    config_path = root / "examples.toml"

    cfg = _load_tests_config(config_path)
    base_tests = cfg.tests.base
    ignored_tests = cfg.tests.ignored

    every_tests = [*base_tests, *ignored_tests]
    _validate_example_list(root, every_tests)

    tests_to_run = base_tests
    if test_name:
        if test_name not in every_tests:
            raise click.BadParameter(f"unknown example {test_name}")
        tests_to_run = [test_name]

    failed_tests = []

    for example_name in tests_to_run:
        test_dir = root / example_name
        print(test_dir.resolve())
        try:
            run_cmd(
                sys.executable,
                "-m",
                "robotpy",
                "test",
                "--builtin",
                cwd=test_dir,
            )
        except subprocess.CalledProcessError:
            print(f"Test in {test_dir.resolve()} failed")
            failed_tests.append(example_name)
            if exitfirst:
                break

    if failed_tests:
        print("Failed tests:")
        for name in failed_tests:
            print(f"- {name}")
        sys.exit(1)

    print("All tests successful!")
