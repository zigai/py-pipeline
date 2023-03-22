import inspect
import re

import docstring_parser
from stdl.str_u import snake_case

from pypipeline.pipeline_action import PipelineAction


def get_pattern_type(pattern: str):
    """Returns whether the pattern is a glob or regex pattern."""
    if "*" in pattern or "?" in pattern:
        return "glob"
    elif re.match(r"^.*(\[.*\]|\\.|\\\|[\w])+.*$", pattern):
        return "regex"
    else:
        return None


def get_command_abbrev(name: str, taken: list[str]) -> str | None:
    """
    Tries to return a short name for a command.
    Returns None if it cannot find a short name.
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


def get_taken_abbrevs(*actions: PipelineAction) -> list[str]:
    taken = []
    for i in actions:
        if i.abbrev is None:
            continue
        if i.abbrev in taken:
            raise ValueError(i.abbrev)
        taken.append(i.abbrev)
    return taken


def fill_missing_abbrevs(*actions: PipelineAction, taken: list[str]):
    for i in actions:
        if i.abbrev is None:
            i.abbrev = get_command_abbrev(snake_case(i.__class__.__name__), taken=taken)


def get_action_description(action: PipelineAction):
    doc = inspect.getdoc(action)
    if doc is None:
        return ""
    doc = docstring_parser.parse(doc)
    if doc.short_description:
        return doc.short_description
    if doc.long_description:
        return doc.long_description
    return ""
