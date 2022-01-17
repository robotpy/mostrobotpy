
#pragma once
#include <robotpy_build.h>
#include <frc2/command/Command.h>
#include <frc2/command/Subsystem.h>

std::vector<std::shared_ptr<frc2::Command>> pyargs2cmdList(py::args cmds);

std::vector<std::shared_ptr<frc2::Subsystem>> pyargs2SharedSubsystemList(py::args subs);

std::vector<frc2::Subsystem*> pyargs2SubsystemList(py::args subs);

template <typename T>
std::shared_ptr<T> convertToSharedPtrHack(T *orig) {
    py::gil_scoped_acquire gil;

    py::object pyo = py::cast(orig);
    return py::cast<std::shared_ptr<T>>(pyo);
}