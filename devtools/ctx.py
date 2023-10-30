import pathlib
import sysconfig
import typing

import toposort

from . import config
from .subproject import Subproject


class Context:
    """Global context used by all rdev commands"""

    def __init__(self) -> None:
        self.root_path = pathlib.Path(__file__).parent.parent
        self.subprojects_path = self.root_path / "subprojects"
        self.cfgpath = self.root_path / "rdev.toml"
        self.cfg, self.rawcfg = config.load(self.cfgpath)

        self.is_roborio = sysconfig.get_platform() == "linux-roborio"

        self.wheel_path = self.root_path / "dist"

        subprojects: typing.List[Subproject] = []
        for project, cfg in self.cfg.subprojects.items():
            # Skip projects that aren't compatible with roborio
            if self.is_roborio and not cfg.roborio:
                continue

            subprojects.append(Subproject(cfg, self.subprojects_path / project))

        # Create a sorted dictionary of subprojects ordered by build order
        si = {p.pyproject_name: i for i, p in enumerate(subprojects)}
        ti = {
            i: [si[r.name] for r in p.requires if r.name in si]
            for i, p in enumerate(subprojects)
        }

        self.subprojects = {
            subprojects[i].name: subprojects[i]
            for i in toposort.toposort_flatten(ti, sort=False)
        }
