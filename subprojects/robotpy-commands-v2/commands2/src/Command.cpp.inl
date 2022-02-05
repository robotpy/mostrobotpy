
// Decorators taken from Java

#define DECORATOR_NOTE \
  "\n" \
  "Note: This decorator works by composing this command within a CommandGroup. The command\n" \
  "cannot be used independently after being decorated, or be re-decorated with a different\n" \
  "decorator, unless it is manually cleared from the list of grouped commands with Command.setGrouped(False)\n" \
  "The decorated command can, however, be further decorated without issue\n"


cls_Command
  .def("andThen",
    [](std::shared_ptr<Command> self, std::function<void()> toRun, wpi::span<std::shared_ptr<Subsystem>> requirements) {
      std::vector<std::shared_ptr<Command>> temp;
      temp.emplace_back(self);
      temp.emplace_back(
          std::make_shared<InstantCommand>(std::move(toRun), requirements));
      return SequentialCommandGroup(std::move(temp));
    },
    py::arg("toRun"), py::arg("requirements") = wpi::span<std::shared_ptr<Subsystem>>{},
    "Decorates this command with a runnable to run after the command finishes.\n"
    DECORATOR_NOTE)
  .def("andThen",
    [](std::shared_ptr<Command> self, py::args cmds) {
      std::vector<std::shared_ptr<Command>> commands;
      commands.emplace_back(self);
      for (auto cmd : cmds) {
        auto cmdptr = py::cast<std::shared_ptr<Command>>(cmd);
        commands.emplace_back(cmdptr);
      }
      return std::make_shared<SequentialCommandGroup>(std::move(commands));
    },
    "Decorates this command with a set of commands to run after it in sequence. Often more\n"
    "convenient/less-verbose than constructing a new :class:`.SequentialCommandGroup` explicitly.\n"
    DECORATOR_NOTE)
  .def("alongWith",
    [](std::shared_ptr<Command> self, py::args cmds) {
      std::vector<std::shared_ptr<Command>> commands;
      commands.emplace_back(self);
      for (auto cmd : cmds) {
        auto cmdptr = py::cast<std::shared_ptr<Command>>(cmd);
        commands.emplace_back(cmdptr);
      }
      return std::make_shared<ParallelCommandGroup>(std::move(commands));
    },
    "Decorates this command with a set of commands to run parallel to it, "
    "ending when the last\n"
    "command ends. Often more convenient/less-verbose than constructing a new\n"
    "ParallelCommandGroup explicitly.\n"
    DECORATOR_NOTE)
  .def("asProxy",
    [](std::shared_ptr<Command> self) {
      return std::make_shared<ProxyScheduleCommand>(self);
    },
    "Decorates this command to run \"by proxy\" by wrapping it in a\n"
    "ProxyScheduleCommand. This is useful for \"forking off\" from command groups\n"
    "when the user does not wish to extend the command's requirements to the\n"
    "entire command group.\n"
    "\n"
    ":returns: the decorated command\n"
    DECORATOR_NOTE
  )
  .def("beforeStarting",
    [](std::shared_ptr<Command> self, std::function<void()> toRun, wpi::span<std::shared_ptr<Subsystem>> requirements) {
      std::vector<std::shared_ptr<Command>> temp;
      temp.emplace_back(std::make_shared<InstantCommand>(std::move(toRun), requirements));
      temp.emplace_back(self);
      return std::make_shared<SequentialCommandGroup>(std::move(temp));
    },
    py::arg("toRun"), py::arg("requirements")=wpi::span<std::shared_ptr<Subsystem> >{},
    "Decorates this command with a runnable to run before this command starts.\n"
    "\n"
    ":param toRun:        the Runnable to run\n"
    ":param requirements: the required subsystems\n"
    "\n"
    ":returns: the decorated command\n"
    DECORATOR_NOTE)
  .def("deadlineWith",
    [](std::shared_ptr<Command> self, py::args cmds) {
      return std::make_shared<ParallelDeadlineGroup>(
        self, std::move(pyargs2cmdList(cmds)));
    },
    "Decorates this command with a set of commands to run parallel to it, ending when the calling\n"
    "command ends and interrupting all the others. Often more convenient/less-verbose than\n"
    "constructing a new :class:`.ParallelDeadlineGroup` explicitly.\n"
    DECORATOR_NOTE)
  .def("perpetually", 
    [](std::shared_ptr<Command> self) {
      return std::make_shared<PerpetualCommand>(self);
    },
    "Decorates this command to run perpetually, ignoring its ordinary end\n"
    "conditions.  The decorated command can still be interrupted or canceled.\n"
    "\n"
    ":returns: the decorated command\n"
    DECORATOR_NOTE)
  .def("raceWith",
    [](std::shared_ptr<Command> self, py::args cmds) {
      std::vector<std::shared_ptr<Command>> commands;
      commands.emplace_back(self);
      for (auto cmd : cmds) {
        auto cmdptr = py::cast<std::shared_ptr<Command>>(cmd);
        commands.emplace_back(cmdptr);
      }
      return std::make_shared<ParallelRaceGroup>(std::move(commands));
    },
    "Decorates this command with a set of commands to run parallel to it, ending when the first\n"
    "command ends. Often more convenient/less-verbose than constructing a new\n"
    "ParallelRaceGroup explicitly.\n"
    DECORATOR_NOTE)
  .def("until",
    [](std::shared_ptr<Command> self, std::function<bool()> condition) {
      std::vector<std::shared_ptr<Command>> temp;
      temp.emplace_back(std::make_shared<WaitUntilCommand>(std::move(condition)));
      temp.emplace_back(self);
      return std::make_shared<ParallelRaceGroup>(std::move(temp));
    },
    py::arg("condition"),
    "Decorates this command with an interrupt condition.  If the specified\n"
    "condition becomes true before the command finishes normally, the command\n"
    "will be interrupted and un-scheduled. Note that this only applies to the\n"
    "command returned by this method; the calling command is not itself changed.\n"
    "\n"
    ":param condition: the interrupt condition\n"
    "\n"
    ":returns: the command with the interrupt condition added\n"
    DECORATOR_NOTE)
  .def("withInterrupt",
    [](std::shared_ptr<Command> self, std::function<bool()> condition) {
      std::vector<std::shared_ptr<Command>> temp;
      temp.emplace_back(std::make_shared<WaitUntilCommand>(std::move(condition)));
      temp.emplace_back(self);
      return std::make_shared<ParallelRaceGroup>(std::move(temp));
    },
    py::arg("condition"),
    "Decorates this command with an interrupt condition.  If the specified\n"
    "condition becomes true before the command finishes normally, the command\n"
    "will be interrupted and un-scheduled. Note that this only applies to the\n"
    "command returned by this method; the calling command is not itself changed.\n"
    "\n"
    ":param condition: the interrupt condition\n"
    "\n"
    ":returns: the command with the interrupt condition added\n"
    DECORATOR_NOTE)
  .def("withTimeout",
    [](std::shared_ptr<Command> self, units::second_t duration) {
      std::vector<std::shared_ptr<Command>> temp;
      temp.emplace_back(std::make_shared<WaitCommand>(duration));
      temp.emplace_back(self);
      return std::make_shared<ParallelRaceGroup>(std::move(temp));
    },
    py::arg("duration"),
    "Decorates this command with a timeout.  If the specified timeout is\n"
    "exceeded before the command finishes normally, the command will be\n"
    "interrupted and un-scheduled.  Note that the timeout only applies to the\n"
    "command returned by this method; the calling command is not itself changed.\n"
    "\n"
    ":param duration: the timeout duration\n"
    "\n"
    ":returns: the command with the timeout added\n"
    DECORATOR_NOTE)
  ;
  
