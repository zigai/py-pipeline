import re
import sys
from typing import Literal

from stdl import fs
from stdl.str_u import snake_case

from pypipeline.action import Action


def get_pattern_type(pattern: str) -> Literal["glob", "regex", None]:
    """Returns whether the pattern is a glob or regex pattern."""
    if "*" in pattern or "?" in pattern:
        return "glob"
    elif re.match(r"^.*(\[.*\]|\\.|\\\|[\w])+.*$", pattern):
        return "regex"
    else:
        return None


def get_abbreviation(name: str, taken: list[str]) -> str | None:
    """
    Tries to return a short name for a command.
    Returns None if it cannot find a short name.

    Args:
        name (str): The name of the command.
        taken (list[str]): A list of taken abbreviations.

    Example:
        >>> get_command_short_name("hello_world", [])
        >>> "h"
        >>> get_command_short_name("hello_world", ["h"])
        >>> "hw"
        >>> get_command_short_name("hello_world", ["hw", "h"])
        >>> "he"
        >>> get_command_short_name("hello_world", ["hw", "h", "he"])
        >>> None
    """
    if name in taken:
        raise ValueError(f"Command name '{name}' already taken")
    if len(name) < 3:
        return None
    name_split = name.split("_")
    abbrev = name_split[0][0]
    if abbrev not in taken and abbrev != name:
        taken.append(abbrev)
        return abbrev
    short_name = "".join([i[0] for i in name_split])
    if short_name not in taken and short_name != name:
        taken.append(short_name)
        return short_name
    try:
        short_name = name_split[0][:2]
        if short_name not in taken and short_name != name:
            taken.append(short_name)
            return short_name
        return None
    except IndexError:
        return None


def get_taken_abbreviations(actions: list[Action]) -> list[str]:
    """
    Returns a list of taken abbreviations for a list of actions.
    """
    taken = []
    for i in actions:
        if i.abbrev is None:
            continue
        if i.abbrev in taken:
            raise ValueError(i.abbrev)
        taken.append(i.abbrev)
    return taken


def fill_missing_abbreviations(actions: list[Action], taken: list[str]) -> None:
    """
    Fills in missing abbreviations for a list of actions.
    """
    for i in actions:
        if i.abbrev is None:
            i.abbrev = get_abbreviation(snake_case(i.__class__.__name__), taken=taken)


def get_executable_name(*, full=False) -> str:
    if full:
        return sys.argv[0]
    return sys.argv[0].split(fs.SEP)[-1]
