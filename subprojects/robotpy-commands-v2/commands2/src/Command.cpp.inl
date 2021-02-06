
// Decorators taken from Java

#define DECORATOR_NOTE \
  "\n" \
  "Note: This decorator works by composing this command within a CommandGroup. The command\n" \
  "cannot be used independently after being decorated, or be re-decorated with a different\n" \
  "decorator, unless it is manually cleared from the list of grouped commands with Command.setGrouped(False)\n" \
  "The decorated command can, however, be further decorated without issue\n"


cls_Command
  .def("andThen",
    [](Command* self, py::args cmds) {
      std::vector<std::shared_ptr<Command>> commands;
      commands.emplace_back(self->shared_from_this());
      for (auto cmd : cmds) {
        auto cmdptr = py::cast<std::shared_ptr<Command>>(cmd);
        commands.emplace_back(cmdptr);
      }
      return std::make_shared<SequentialCommandGroup>(std::move(commands));
    },
    "Decorates this command with a set of commands to run after it in sequence. Often more\n"
    "convenient/less-verbose than constructing a new {@link SequentialCommandGroup} explicitly.\n"
    DECORATOR_NOTE)
  .def("alongWith",
    [](Command* self, py::args cmds) {
      std::vector<std::shared_ptr<Command>> commands;
      commands.emplace_back(self->shared_from_this());
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
  .def("deadlineWith",
    [](Command* self, py::args cmds) {
      return std::make_shared<ParallelDeadlineGroup>(
        self->shared_from_this(), std::move(pyargs2cmdList(cmds)));
    },
    "Decorates this command with a set of commands to run parallel to it, ending when the calling\n"
    "command ends and interrupting all the others. Often more convenient/less-verbose than\n"
    "constructing a new {@link ParallelDeadlineGroup} explicitly.\n"
    DECORATOR_NOTE)
  .def("raceWith",
    [](Command* self, py::args cmds) {
      std::vector<std::shared_ptr<Command>> commands;
      commands.emplace_back(self->shared_from_this());
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
  ;
  
