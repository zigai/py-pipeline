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


def get_taken_abbrevs(*actions: PipelineAction):
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


def get_description(action: PipelineAction):
    doc = inspect.getdoc(action)
    if doc is None:
        return ""
    doc = docstring_parser.parse(doc)
    if doc.short_description:
        return doc.short_description
    if doc.long_description:
        return doc.long_description
    return ""


RESERVED_ARGS = ["help", "t"]


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
        print_res=True,
        run=True,
    ) -> None:
        self.filters = filters or []
        self.transformers = transformers or []
        self.taken_abbrevs = get_taken_abbrevs(*self.filters, *self.transformers)
        fill_missing_abbrevs(*self.filters, *self.transformers, taken=self.taken_abbrevs)
        self.description = description or ""
        self.print_res = print_res
        self.commands = {}
        self.help = None
        self.t = cpu_count() - 1
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
        print(colored(f"[{self.name}] {message}", "red"))

    def log_info(self, message: str):
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
            "  -t".ljust(ljust) + f"   number of threads to use (default: {cpu_count() - 1})"
        )

        flags_help.append("\nfilters:")
        for f, flag_help in zip(self.filters, part1_filters):
            flags_help.append(f"{flag_help}   {get_description(f)}")

        flags_help.append("\ntransformers:")
        for t, flag_help in zip(self.transformers, part1_transformers):
            flags_help.append(f"{flag_help}   {get_description(t)}")

        self.help = self.get_help_str(flags_help)

    def get_help_str(self, flags_help: list[str]):
        return self.description + "\n" + self.base_description + "\n".join(flags_help)

    def parse_args(self) -> tuple[list[str], list[PipelineAction]]:
        args = sys.argv[1:]
        if not args:
            print(self.help)
            sys.exit(1)

        items = []
        actions = []
        i = 0
        while i < len(args):
            arg = args[i]
            if len(arg) > 1 and arg[1:] in self.valid_command_names:
                if arg == "-help":
                    print(self.help)
                    sys.exit(1)
                if arg == "-t":
                    self.t = int(args[i + 1])
                    i += 1
                    # continue
                if arg[1:] in self.commands:
                    cmd = arg[1:]
                    inverted = cmd.endswith("!")
                    cmd_args = args[i + 1]
                    if inverted:
                        action = self.commands[cmd].parse(cmd_args, invert=True)
                    else:
                        action = self.commands[cmd].parse(cmd_args)

                    actions.append(action)
                    i += 1
                    # continue
                else:
                    self.log_error(f"unknown command: {arg}")
                    sys.exit(1)
            else:
                if not arg.startswith("-"):
                    items.append(arg)
                else:
                    self.log_error(f"unknown argument: {arg}")
                    sys.exit(1)
            i += 1
        return items, actions

    def collect_items(self, items: list[str]) -> list[PipelineItem]:
        raise NotImplementedError

    def print_result(self, items: ItemsContainer):
        for item in items.kept:
            print(item)

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
        return self.pipeline_cls(actions=actions)

    def run(self):
        items, actions = self.parse_args()
        if items is None or actions is None:
            self.log_error("no actions provided")
            sys.exit(1)

        items = self.collect_items(items)
        if not items:
            self.log_info("no items to process")
            sys.exit(0)

        processed_items = self._process_items(items, actions)

        if self.print_res:
            self.print_result(processed_items)


__all__ = ["PyPipelineCLI"]
