# notrack
class IllegalCommandUse(Exception):
    """
    This exception is raised when a command is used in a way that it shouldn't be.

    You shouldn't try to catch this exception, if it occurs it means your code is
    doing something it probably shouldn't be doing
    """
