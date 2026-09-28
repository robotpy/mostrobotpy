from pathlib import Path

import wpilog
from wpimath import Pose2d, Rotation2d
from wpiutil import wpistruct


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


def test_iter_auto_generates_native_pose2d_value_before_schema(tmp_path: Path):
    first_pose = Pose2d(1.25, -2.5, Rotation2d(0.5))
    second_pose = Pose2d(-3.0, 4.5, Rotation2d(-0.75))
    path = tmp_path / "native-pose-before-schema.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        pose_entry = log.start("/pose", "struct:Pose2d", "", 1)
        log.append_raw(pose_entry, wpistruct.pack(first_pose), 2)
        wpistruct.for_each_nested(
            Pose2d,
            lambda type_string, schema: log.add_schema(
                type_string, "structschema", schema
            ),
        )
        log.append_raw(pose_entry, wpistruct.pack(second_pose), 6)

    values = list(wpilog.DataLogReader(str(path)).iter_auto())

    assert [entry.type for _, entry, _ in values] == [
        "struct:Pose2d",
        "structschema",
        "structschema",
        "structschema",
        "struct:Pose2d",
    ]
    first, generated_translation, generated_rotation, generated_pose, second = [
        value for _, _, value in values
    ]
    assert type(first) is generated_pose
    assert type(second) is generated_pose
    assert type(first.translation) is generated_translation
    assert type(first.rotation) is generated_rotation
    assert type(second.translation) is generated_translation
    assert type(second.rotation) is generated_rotation
    assert (first.translation.x, first.translation.y, first.rotation.value) == (
        1.25,
        -2.5,
        0.5,
    )
    assert (second.translation.x, second.translation.y, second.rotation.value) == (
        -3.0,
        4.5,
        -0.75,
    )
