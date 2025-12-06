import shlex
import subprocess
import sys
import typing

from validobj import errors
import validobj.validation

T = typing.TypeVar("T")


class ValidationError(Exception):
    pass


def _convert_validation_error(fname, ve: errors.ValidationError) -> ValidationError:
    locs = []
    msg = []

    e = ve
    while e is not None:

        if isinstance(e, errors.WrongFieldError):
            locs.append(f".{e.wrong_field}")
        elif isinstance(e, errors.WrongListItemError):
            locs.append(f"[{e.wrong_index}]")
        else:
            msg.append(str(e))

        e = e.__cause__

    loc = "".join(locs)
    if loc.startswith("."):
        loc = loc[1:]
    msg = "\n  ".join(msg)
    vmsg = f"{fname}: {loc}:\n  {msg}"
    return ValidationError(vmsg)


def parse_input(value: typing.Any, spec: typing.Type[T], fname) -> T:
    try:
        return validobj.validation.parse_input(value, spec)
    except errors.ValidationError as ve:
        raise _convert_validation_error(fname, ve) from None


def run_cmd(*args: str, cwd=None, check=True):
    print("+", shlex.join(args))
    return subprocess.run(args, cwd=cwd, check=check)
