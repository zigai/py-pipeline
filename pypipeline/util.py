import re


def get_pattern_type(pattern: str):
    """Returns whether the pattern is a glob or regex pattern."""
    if "*" in pattern or "?" in pattern:
        return "glob"
    elif re.match("^.*(\[.*\]|\\.|\\\|[\w])+.*$", pattern):
        return "regex"
    else:
        return None
