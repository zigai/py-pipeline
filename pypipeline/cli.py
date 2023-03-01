import inspect
import sys
from multiprocessing import cpu_count

import docstring_parser
from interfacy_cli.cli import get_command_abbrev
from stdl.str_u import colored, kebab_case, snake_case

from pypipeline.filter import Filter
from pypipeline.pipeline import Pipeline
from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem


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
    cmd_prefix = "-"
    pipeline_cls = Pipeline
    name = "PyPipeline"

    def __init__(
        self,
        filters: list | None = None,
        description=None,
        transformers: list | None = None,
        print_result=True,
    ) -> None:
        self.filters = filters or []
        self.transformers = transformers or []
        self.taken_abbrevs = get_taken_abbrevs(*self.filters, *self.transformers)
        fill_missing_abbrevs(*self.filters, *self.transformers, taken=self.taken_abbrevs)
        self.description = description or ""
        self.print_result = print_result
        self.commands = {}
        self.help = None
        self.t = cpu_count() - 1
        self._build()
        self.valid_command_names = list(self.commands.keys())
        self.valid_command_names.extend(RESERVED_ARGS)

    def _build_help_cmd_names(self, actions: list[PipelineAction]):
        command_names = []
        for f in actions:
            command_long = kebab_case(f.__name__)  # type: ignore
            if f.abbrev is None:
                command_short = command_long
                command_names.append(f"  {self.cmd_prefix}{command_short}")
                self.commands[command_short] = f
                if issubclass(f, Filter):
                    self.commands["!" + command_short] = f
                continue
            command_short = f.abbrev
            self.commands[command_long] = f
            self.commands[command_short] = f
            if issubclass(f, Filter):
                self.commands["!" + command_long] = f
                self.commands["!" + command_short] = f
            command_names.append(
                f"  {self.cmd_prefix}{command_short}, {self.cmd_prefix}{command_long}"
            )
        return command_names

    def log_error(self, message: str):
        print(colored(f"[{self.name}] {message}", "red"))

    def log_info(self, message: str):
        print(f"[{self.name}] {message}")

    def _build(self):
        helpstr = []

        part1_filters = self._build_help_cmd_names(self.filters)
        part1_transformers = self._build_help_cmd_names(self.transformers)
        mx_len_filters = max([len(i) for i in part1_filters])
        mx_len_transformers = max([len(i) for i in part1_transformers])

        ljust = max(mx_len_filters, mx_len_transformers, self.min_ljust)
        ljust = min(ljust, self.max_ljust)
        part1_filters = [i.ljust(ljust) for i in part1_filters]
        part1_transformers = [i.ljust(ljust) for i in part1_transformers]

        helpstr.append("options:")
        helpstr.append("  -help".ljust(ljust) + "   show this help message and exit")
        helpstr.append("  -t".ljust(ljust) + "   number of threads to use (default: cpu_count - 1)")

        helpstr.append("\nfilters:")
        for f, cmd_help in zip(self.filters, part1_filters):
            helpstr.append(f"{cmd_help}   {get_description(f)}")

        helpstr.append("\ntransformers:")
        for t, cmd_help in zip(self.transformers, part1_transformers):
            helpstr.append(f"{cmd_help}   {get_description(t)}")

        self.help = self.description + "\n".join(helpstr)

    def parse_args(self) -> tuple[list[str], list[PipelineAction]]:
        args = sys.argv[1:]
        if not args:
            print(self.help)
            exit(1)
        items = []
        actions = []
        i = 0
        while i < len(args):
            arg = args[i]
            if len(arg) > 1 and arg[1:] in self.valid_command_names:
                if arg == "-help":
                    print(self.help)
                    exit(1)
                if arg == "-t":
                    self.t = int(args[i + 1])
                    i += 1
                    continue
                if arg[1:] in self.commands:
                    arg = arg[1:]
                    inverted = arg.startswith("!")
                    if inverted:
                        action = self.commands[arg](args[i + 1], invert=True)
                    else:
                        action = self.commands[arg](args[i + 1])
                    actions.append(action)
                    i += 1
                    continue
                else:
                    self.log_error(f"unknown command: {arg}")
                    exit(1)
            else:
                if not arg.startswith("-"):
                    items.append(arg)
                else:
                    self.log_error(f"unknown argument: {arg}")
                    exit(1)
            i += 1
        return items, actions

    def collect_items(self, items: list[str]) -> list[PipelineItem]:
        raise NotImplementedError

    def run(self):
        items, actions = self.parse_args()
        if items is None or actions is None:
            return
        items = self.collect_items(items)
        if not items:
            self.log_info("no items to process")
            exit(0)
        pipeline = self.pipeline_cls(actions=actions)
        res = pipeline.process_multi(items, t=self.t)
        if self.print_result:
            for item in res:
                print(item)


__all__ = ["PyPipelineCLI"]
