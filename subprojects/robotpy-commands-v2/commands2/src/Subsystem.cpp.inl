
cls_Subsystem.
  def("setDefaultCommand", [](std::shared_ptr<Subsystem> self, std::shared_ptr<Command> defaultCommand) {
      CommandScheduler::GetInstance().SetDefaultCommand(self, defaultCommand);
    },
    py::arg("defaultCommand"), release_gil(), py::doc(
    "Sets the default Command of the subsystem.  The default command will be\n"
    "automatically scheduled when no other commands are scheduled that require\n"
    "the subsystem. Default commands should generally not end on their own, i.e.\n"
    "their IsFinished() method should always return false.  Will automatically\n"
    "register this subsystem with the CommandScheduler.\n"
    "\n"
    ":param defaultCommand: the default command to associate with this subsystem")
  );