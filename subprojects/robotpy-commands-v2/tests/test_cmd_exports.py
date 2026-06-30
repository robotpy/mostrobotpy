import re

import commands2.cmd


def test_cmd_all_entries_exist_and_are_snake_case():
    for name in commands2.cmd.__all__:
        assert hasattr(commands2.cmd, name), f"commands2.cmd.__all__ entry {name!r} does not exist"
        assert re.fullmatch(r"[a-z_][a-z0-9_]*", name), (
            f"commands2.cmd.__all__ entry {name!r} is not snake_case"
        )
