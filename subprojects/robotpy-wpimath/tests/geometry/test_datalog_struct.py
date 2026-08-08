from pathlib import Path

import wpilog
from wpimath import Pose2d, Rotation2d


def test_iter_auto_supplied_native_pose2d(tmp_path: Path):
    pose = Pose2d(1.0, 2.0, Rotation2d())
    path = tmp_path / "native-struct.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructLogEntry(log, "/pose", Pose2d).append(pose, 10)

    decoded = [
        value
        for _, entry, value in wpilog.DataLogReader(str(path)).iter_auto(Pose2d)
        if entry is not None and entry.type == "struct:Pose2d"
    ]
    assert decoded == [pose]
