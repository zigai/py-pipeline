import inspect
import sys
from multiprocessing import cpu_count

import docstring_parser
from stdl.str_u import colored, kebab_case, snake_case

from pypipeline.filter import Filter
from pypipeline.items_container import ItemsContainer
from pypipeline.pipeline import Pipeline
from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem

RESERVED_ARGS = ["help", "t", "v", "verbose", "mode"]


class ExitCodes:
    SUCCESS = 0
    INPUT_ERROR = 1
    PARSING_ERROR = 2
    PROCESSING_ERROR = 3


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


from typing import Literal


class PyPipelineCLI:
    min_ljust = 8
    max_ljust = 24
    flag_prefix = "-"
    pipeline_cls = Pipeline
    base_description = "Filters can be inverted by adding a '!' after the flag .\n"
    name = "PyPipeline"

    def __init__(
        self,
        filters: list | None = None,
        transformers: list | None = None,
        description: str = None,  # type: ignore
        mode: Literal["kept", "discarded"] = "kept",
        print_res=True,
        run=True,
    ) -> None:
        self.mode = mode
        self.filters = filters or []
        self.transformers = transformers or []
        self.description = description or ""
        self.print_res = print_res
        self.err_label = colored(f"[{self.name}]", "red")
        self.commands = {}
        self.help = None
        self.t = cpu_count() - 1
        self.verbose = False

        self.taken_abbrevs = get_taken_abbrevs(*self.filters, *self.transformers)
        fill_missing_abbrevs(*self.filters, *self.transformers, taken=self.taken_abbrevs)

        self._build_cli()
        self.valid_command_names = list(self.commands.keys())
        self.valid_command_names.extend(RESERVED_ARGS)

        if run:
            self.run()

    def _build_help_cmd_names(self, actions: list[PipelineAction]) -> list[str]:
        command_names = []
        for action in actions:
            flag_long = kebab_case(action.__name__)  # type: ignore
            if action.abbrev is None:
                flag_short = flag_long
                command_names.append(f"  {self.flag_prefix}{flag_short}")
                self.commands[flag_short] = action
                if issubclass(action, Filter):
                    self.commands[flag_short + "!"] = action
                continue

            flag_short = action.abbrev
            self.commands[flag_long] = action
            self.commands[flag_short] = action

            if issubclass(action, Filter):
                self.commands[flag_long + "!"] = action
                self.commands[flag_short + "!"] = action
            command_names.append(f"  {self.flag_prefix}{flag_short}, {self.flag_prefix}{flag_long}")

        return command_names

    def log_error(self, message: str):
        print(f"{self.err_label} {message}", file=sys.stderr)

    def log_info(self, message: str):
        if not self.verbose:
            return
        print(f"[{self.name}] {message}")

    def _build_cli(self):
        flags_help = []

        part1_filters = self._build_help_cmd_names(self.filters)
        part1_transformers = self._build_help_cmd_names(self.transformers)
        mx_len_filters = max([len(i) for i in part1_filters])
        mx_len_transformers = max([len(i) for i in part1_transformers])

        ljust = max(mx_len_filters, mx_len_transformers, self.min_ljust)
        ljust = min(ljust, self.max_ljust)
        part1_filters = [i.ljust(ljust) for i in part1_filters]
        part1_transformers = [i.ljust(ljust) for i in part1_transformers]

        flags_help.append("\noptions:")
        flags_help.append("  -help".ljust(ljust) + "   show this help message and exit")
        flags_help.append(
            "  -mode".ljust(ljust) + "   display kept or discarded items (default: 'kept')"
        )
        flags_help.append(
            "  -t".ljust(ljust) + f"   number of threads to use (default: {cpu_count() - 1})"
        )
        flags_help.append(
            "  -v, -verbose".ljust(ljust) + "   verbose mode (extra log messages and progress bars)"
        )

        flags_help.append("\nfilters:")
        for f, flag_help in zip(self.filters, part1_filters):
            flags_help.append(f"{flag_help}   {get_action_description(f)}")

        flags_help.append("\ntransformers:")
        for t, flag_help in zip(self.transformers, part1_transformers):
            flags_help.append(f"{flag_help}   {get_action_description(t)}")

        self.help = self.get_help_str(flags_help)

    def get_help_str(self, flags_help: list[str]):
        return self.description + "\n" + self.base_description + "\n".join(flags_help)

    def parse_args(self) -> tuple[list[str], list[PipelineAction]]:
        args = sys.argv[1:]
        if not args:
            self.log_error(f"no arguments provided. use -help flag for help")
            sys.exit(ExitCodes.INPUT_ERROR)

        items, actions = [], []
        i = 0
        while i < len(args):
            arg = args[i]
            if len(arg) > 1 and arg[1:] in self.valid_command_names:
                if arg == "-help":
                    print(self.help)
                    sys.exit(ExitCodes.SUCCESS)
                if arg == "-t":
                    self.t = int(args[i + 1])
                    i += 1
                if arg in ["-v", "-verbose"]:
                    self.verbose = True
                if arg == "-mode":
                    self.mode = args[i + 1]
                    if not self.mode in ["kept", "discarded"]:
                        self.log_error(f"invalid mode: {self.mode}")
                        sys.exit(ExitCodes.INPUT_ERROR)
                    i += 1
                if arg[1:] in self.commands:
                    cmd = arg[1:]
                    cmd_args = args[i + 1]
                    inverted = cmd.endswith("!")
                    action = self.commands[cmd].parse(
                        cmd_args, **{"invert": inverted} if inverted else {}
                    )
                    actions.append(action)
                    i += 1
                else:
                    self.log_error(f"unknown command: {arg}")
                    sys.exit(ExitCodes.PARSING_ERROR)
            else:
                if not arg.startswith("-"):
                    items.append(arg)
                else:
                    self.log_error(f"unknown argument: {arg}")
                    sys.exit(ExitCodes.PARSING_ERROR)
            i += 1
        return items, actions

    def _process_items(self, items: list[PipelineItem], actions: list[PipelineAction]):
        pipeline = self._create_pipeline(actions)
        if self.t != 1:
            if len(items) < self.t:
                self.log_info(
                    f"number of items is less than number of threads, using {len(items)} thread(s)"
                )
                self.t = len(items)
            res = pipeline.process_multi(items, t=self.t)
        else:
            res = pipeline.process(items)
        return res

    def _create_pipeline(self, actions: list[PipelineAction]):
        return self.pipeline_cls(actions=actions, verbose=self.verbose)

    def collect_items(self, items: list[str]) -> list[PipelineItem]:
        raise NotImplementedError

    def print_result(self, items: ItemsContainer):
        if self.mode == "kept":
            for item in items.kept:
                print(item)
        else:
            for i in items.discarded:
                print(i)

    def run(self):
        try:
            items, actions = self.parse_args()
        except Exception as e:
            self.log_error(f"error while parsing arguments: {e}")
            sys.exit(ExitCodes.PARSING_ERROR)

        if items is None or actions is None:
            self.log_error("no actions provided. use -help flag for help")
            sys.exit(ExitCodes.INPUT_ERROR)

        try:
            items = self.collect_items(items)
        except Exception as e:
            self.log_error(f"error while collecting items: {e}")
            sys.exit(ExitCodes.INPUT_ERROR)

        if not items:
            self.log_info("no items to process found")
            sys.exit(ExitCodes.INPUT_ERROR)

        try:
            processed_items = self._process_items(items, actions)
        except Exception as e:
            self.log_error(f"error while processing items: {e}")
            sys.exit(1)
        if self.print_res:
            self.print_result(processed_items)
        sys.exit(ExitCodes.SUCCESS)


__all__ = ["PyPipelineCLI"]
