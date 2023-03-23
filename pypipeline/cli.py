import inspect
import sys
from multiprocessing import cpu_count
from typing import Literal

from stdl.str_u import colored, kebab_case

from pypipeline.filter import Filter
from pypipeline.items_container import ItemsContainer
from pypipeline.pipeline import Pipeline
from pypipeline.pipeline_action import PipelineAction, get_action_description
from pypipeline.pipeline_item import PipelineItem
from pypipeline.util import fill_missing_abbrevs, get_executable_name, get_taken_abbrevs

RESERVED_ARGS = ["help", "t", "v", "verbose", "mode"]


def get_action_help(action: PipelineAction):
    docstr = inspect.getdoc(action)
    action_type = "Filter" if issubclass(action, Filter) else "Transformer"
    action_name = kebab_case(action.__name__)
    action_abbrev = action.abbrev
    return f"{action_name} | {action_type} | Abbrev='{action_abbrev}' | Priority={action.priority}\n\n{docstr}"


class ExitCodes:
    SUCCESS = 0
    INPUT_ERROR = 1
    PARSING_ERROR = 2
    PROCESSING_ERROR = 3


class PyPipelineCLI:
    min_ljust = 8
    max_ljust = 24
    flag_prefix_short = "-"
    flag_prefix_long = "--"
    pipeline_cls = Pipeline

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
        self.available_actions: dict[str, PipelineAction] = {}
        self.help = None
        self.t = cpu_count() - 1
        self.verbose = False
        self.items = []
        self.executable = get_executable_name()
        self.taken_abbrevs = get_taken_abbrevs(*self.filters, *self.transformers)
        fill_missing_abbrevs(*self.filters, *self.transformers, taken=self.taken_abbrevs)

        self._build_cli()
        self.valid_action_names = list(self.available_actions.keys())

        if run:
            self.run()

    def _collect_actions(self, actions: list[PipelineAction]) -> list[str]:
        names = []
        for action in actions:
            flag_long = kebab_case(action.__name__)  # type: ignore
            if action.abbrev is None:
                flag_short = flag_long
                names.append(f"  {self.flag_prefix_short}{flag_short}")
                self.available_actions[flag_short] = action
                if issubclass(action, Filter):  # type:ignore
                    self.available_actions[flag_short + "!"] = action
                continue

            flag_short = action.abbrev
            self.available_actions[flag_long] = action
            self.available_actions[flag_short] = action

            if issubclass(action, Filter):  # type:ignore
                self.available_actions[flag_long + "!"] = action
                self.available_actions[flag_short + "!"] = action
            names.append(
                f"  {self.flag_prefix_short}{flag_short}, {self.flag_prefix_long}{flag_long}"
            )

        return names

    def log_error(self, message: str):
        print(f"{self.err_label} {message}", file=sys.stderr)

    def log_info(self, message: str):
        if not self.verbose:
            return
        print(f"[{self.name}] {message}")

    def _build_cli(self):
        flag_help_filters = self._collect_actions(self.filters)
        flags_help_transformers = self._collect_actions(self.transformers)

        mx_len_filters = max([len(i) for i in flag_help_filters])
        mx_len_transformers = max([len(i) for i in flags_help_transformers])
        ljust = self._get_ljust(mx_len_filters, mx_len_transformers)

        flag_help_filters = [i.ljust(ljust) for i in flag_help_filters]
        flags_help_transformers = [i.ljust(ljust) for i in flags_help_transformers]

        flags_help = self._get_options_help_section(ljust)

        flags_help.append("\nfilters:")
        for action, flag_help in zip(self.filters, flag_help_filters):
            flags_help.append(f"{flag_help}   {get_action_description(action)}")

        flags_help.append("\ntransformers:")
        for action, flag_help in zip(self.transformers, flags_help_transformers):
            flags_help.append(f"{flag_help}   {get_action_description(action)}")

        self.help = self.get_help_str(flags_help)

    def _remove_flag_prefix(self, flag: str) -> str:
        if flag.startswith(self.flag_prefix_long):
            return flag[2:]
        if flag.startswith(self.flag_prefix_short):
            return flag[1:]
        return flag

    def _get_ljust(self, *section_flag_lengths: int) -> int:
        ljust = max(*section_flag_lengths, self.min_ljust)
        ljust = min(ljust, self.max_ljust)
        return ljust

    def _get_usage_section(self) -> str:
        return f"usage: {self.executable} [--help] [-v] [--mode] MODE [-t] T [actions] [items]"

    def _get_usage_notes(self) -> list[str]:
        return [
            f"\n\nnotes:",
            "  filters can be inverted by adding a '!' after the flag",
            f"  you can get help for a specific action by running '{self.executable} <action> --help'\n",
        ]

    def _get_options_help_section(self, ljust: int) -> list[str]:
        return [
            "\noptions:",
            f"  --help".ljust(ljust) + "   show this help message and exit",
            f"  --mode".ljust(ljust)
            + f"   display kept or discarded items (default: '{self.mode}')",
            f"  -t".ljust(ljust) + f"   number of threads to use (default: {self.t})",
            f"  -v, -verbose".ljust(ljust)
            + "   verbose mode (extra log messages and progress bars)",
        ]

    def get_help_str(self, flags_help: list[str]):
        return (
            self._get_usage_section()
            + self.description
            + "\n"
            + "\n".join(flags_help)
            + "\n".join(self._get_usage_notes())
        )

    def parse_args(self) -> list[PipelineAction]:
        args = sys.argv[1:]
        if not args:
            self.log_error(f"no arguments provided. run '{self.executable} --help' for help")
            sys.exit(ExitCodes.INPUT_ERROR)

        actions = []
        i = 0
        while i < len(args):
            arg = self._remove_flag_prefix(args[i])
            if len(arg) > 1 and (arg in self.valid_action_names or arg in RESERVED_ARGS):
                if args[i] == "--help":
                    print(self.help)
                    sys.exit(ExitCodes.SUCCESS)
                if args[i] == "-t":
                    self.t = int(args[i + 1])
                    i += 2
                    continue
                if args[i] in ["-v", "--verbose"]:
                    self.verbose = True
                    i += 1
                    continue
                if args[i] == "--mode":
                    self.mode = args[i + 1]
                    if not self.mode in ["kept", "discarded"]:
                        self.log_error(f"invalid mode: {self.mode}")
                        sys.exit(ExitCodes.INPUT_ERROR)
                    i += 2
                    continue
                if arg in self.available_actions:
                    inverted = arg.endswith("!")
                    action_args = args[i + 1]
                    if action_args == "--help":
                        print(get_action_help(self.available_actions[arg]))
                        sys.exit(ExitCodes.SUCCESS)
                    action = self.available_actions[arg].parse(
                        action_args, **{"invert": inverted} if inverted else {}
                    )
                    actions.append(action)
                    i += 1
                else:
                    self.log_error(f"unknown argument: {args[i]}")
                    sys.exit(ExitCodes.PARSING_ERROR)
            else:
                if not arg.startswith("-"):
                    self.items.append(arg)
                else:
                    self.log_error(f"unknown argument: {args[i]}")
                    sys.exit(ExitCodes.PARSING_ERROR)
            i += 1
        return actions

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
            actions = self.parse_args()
        except Exception as e:
            self.log_error(f"error while parsing arguments: {e}")
            sys.exit(ExitCodes.PARSING_ERROR)

        if actions is None:
            self.log_error(
                f"no actions provided. run '{self.executable} --help' to see available actions"
            )
            sys.exit(ExitCodes.INPUT_ERROR)

        try:
            items = self.collect_items(self.items)
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
