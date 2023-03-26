import sys

SEP = ":"
INT_MAX = sys.maxsize
INT_MIN = -INT_MAX - 1
FLAG_PREFIX_SHORT = "-"
FLAG_PREFIX_LONG = "--"
HELP_INDENT = "  "
RESERVED_FLAGS = ["help", "t", "v", "verbose", "mode"]
FILTER_INVERT_SUFFIX = "!"
CLI_HELP_INDENT = 2
CLI_MIN_LJUST = 8
CLI_MAX_LJUST = 24


class ExitCodes:
    SUCCESS = 0
    INPUT_ERROR = 1
    PARSING_ERROR = 2
    PROCESSING_ERROR = 3
