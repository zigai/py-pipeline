import inspect
import sys
from functools import cached_property
from multiprocessing import cpu_count
from typing import Literal

import docstring_parser
from stdl.fs import read_stdin
from stdl.str_u import colored, kebab_case

from pypipeline.action import Action
from pypipeline.constants import (
    CLI_HELP_INDENT,
    CLI_MAX_LJUST,
    CLI_MIN_LJUST,
    FILTER_INVERT_SUFFIX,
    FLAG_PREFIX_LONG,
    FLAG_PREFIX_SHORT,
    RESERVED_FLAGS,
    ExitCodes,
)
from pypipeline.item import Item
from pypipeline.items_container import ItemsContainer
from pypipeline.pipeline import Pipeline
from pypipeline.util import fill_missing_abbreviations, get_executable_name, get_taken_abbreviations


class ActionContainer:
    def __init__(self, action: Action) -> None:
        self.cls = action

    def __repr__(self) -> str:
        return f"ActionContainer(for:'{self.name}', CLI flags:'{self.cli_help_flag}')"  # type: ignore

    @property
    def name(self):
        return self.cls.__name__  # type:ignore

    @cached_property
    def flag_short(self):
        if not self.cls.abbrev:
            return None
        return FLAG_PREFIX_SHORT + self.cls.abbrev

    @cached_property
    def flag_long(self):
        return FLAG_PREFIX_LONG + kebab_case(self.name)

    @cached_property
    def description(self) -> str:
        doc = self.cls.get_docstr()
        if doc is None:
            return ""
        doc = docstring_parser.parse(doc)
        if doc.short_description:
            return doc.short_description
        if doc.long_description:
            return doc.long_description
        return ""

    @cached_property
    def cli_help_flag(self):
        if self.flag_short is None:
            return f"{CLI_HELP_INDENT * ' '}{self.flag_long}"
        return f"{CLI_HELP_INDENT * ' '}{self.flag_short}, {self.flag_long}"

    def get_help_long(self):
        docstr = inspect.getdoc(self.cls)
        action_name = kebab_case(self.name)
        return f"{action_name} | {self.cls.type} | abbrev='{self.cls.abbrev}' | priority={self.cls.priority}\n\n{docstr}"


class CommandLineActionsManager:
    def __init__(self, actions: list[Action]) -> None:
        actions_abbrevs = get_taken_abbreviations(*actions or [])
        for i in actions_abbrevs:
            if i in RESERVED_FLAGS:
                raise ValueError(f"action abbrevation can't be any of: {', '.join(RESERVED_FLAGS)}")

        self.taken_flags = [*RESERVED_FLAGS, *get_taken_abbreviations(*actions)]
        fill_missing_abbreviations(*actions, taken=self.taken_flags)
        self.cli_action_map: dict[str, ActionContainer] = {}
        self.actions = [ActionContainer(i) for i in actions]
        self.collect_actions()

    def collect_actions(self) -> None:
        for action in self.actions:
            self.cli_action_map[action.flag_long] = action
            if action.flag_short:
                self.cli_action_map[action.flag_short] = action  # type:ignore
            if action.cls.type == "filter":
                self.cli_action_map[action.flag_long + FILTER_INVERT_SUFFIX] = action
                if action.flag_short:
                    self.cli_action_map[
                        action.flag_short + FILTER_INVERT_SUFFIX  # type:ignore
                    ] = action

    @cached_property
    def ljust(self) -> int:
        ljust = max(*[len(i.cli_help_flag) for i in self.actions], CLI_MIN_LJUST)
        ljust = min(ljust, CLI_MAX_LJUST)
        return ljust

    def get_actions_help_section(self) -> str:
        help_filters, help_transformers = ["\nfilters:"], ["\ntransformers:"]
        for i in self.actions:
            h = f"{i.cli_help_flag.ljust(self.ljust)}   {i.description}"
            if i.cls.type == "filter":
                help_filters.append(h)
            elif i.cls.type == "transformer":
                help_transformers.append(h)
            else:
                raise ValueError(i.cls.type)

        return "\n".join([*help_filters, *help_transformers])

    def get(self, name: str):
        return self.cli_action_map.get(name, None)


class PyPipelineCLI:
    pipeline_cls = Pipeline
    name = "PyPipeline"

    def __init__(
        self,
        actions: list[Action],
        description: str = None,  # type: ignore
        mode: Literal["kept", "discarded"] = "kept",
        print_results=True,
        run=True,
        read_from_stdin=True,
    ) -> None:
        self.mode = mode
        self.description = description or ""
        self.print_results = print_results
        self.read_from_stdin = read_from_stdin

        self.err_label = colored(f"[{self.name}]", "red")
        self.executable = get_executable_name()
        self.t = cpu_count() - 1
        self.verbose = False
        self.help = None
        self.items = []

        self.manager = CommandLineActionsManager(actions)
        self.help = self._get_help_str()

        if run:
            self.run()

    def log_error(self, message: str):
        print(f"{self.err_label} {message}", file=sys.stderr)

    def log_info(self, message: str):
        if not self.verbose:
            return
        print(f"[{self.name}] {message}")

    def _remove_prefix(self, flag: str) -> str:
        if flag.startswith(FLAG_PREFIX_LONG):
            return flag[len(FLAG_PREFIX_LONG) :]
        if flag.startswith(FLAG_PREFIX_SHORT):
            return flag[len(FLAG_PREFIX_SHORT) :]
        return flag

    def _get_usage_section(self) -> str:
        return f"usage: {self.executable} [--help] [-v] [--mode] MODE [-t] T [actions] [items]"

    def _get_usage_notes_section(self) -> list[str]:
        return [
            f"\n\nnotes:",
            "  filters can be inverted by adding a '!' after the flag",
            f"  you can get help for a specific action by running '{self.executable} <action> --help'\n",
        ]

    def _get_options_help_section(self, ljust: int) -> list[str]:
        return [
            "\noptions:",
            f"  --help".ljust(ljust) + "   show this help message and exit",
            f"  --mode".ljust(ljust) + f"   display kept/discarded items (default: '{self.mode}')",
            f"  -t".ljust(ljust) + f"   number of threads to use (default: {self.t})",
            f"  -v, -verbose".ljust(ljust)
            + "   verbose mode (extra log messages and progress bars)",
        ]

    def _get_help_str(self):
        return (
            self._get_usage_section()
            + self.description
            + "\n"
            + "\n".join(self._get_options_help_section(self.manager.ljust))
            + "\n"
            + self.manager.get_actions_help_section()
            + "\n".join(self._get_usage_notes_section())
        )

    def parse_args(self) -> list[Action]:
        args = sys.argv[1:]
        if not args:
            self.log_error(f"no arguments provided. run '{self.executable} --help' for help")
            sys.exit(ExitCodes.INPUT_ERROR)

        actions = []
        i = 0
        while i < len(args):
            arg = self._remove_prefix(args[i])
            if arg in RESERVED_FLAGS:
                match arg:
                    case "help":
                        print(self.help)
                        sys.exit(ExitCodes.SUCCESS)
                    case "t":
                        self.t = int(args[i + 1])
                        i += 2
                    case "mode":
                        self.mode = args[i + 1]
                        if not self.mode in ["kept", "discarded"]:
                            self.log_error(f"invalid mode: {self.mode}")
                            sys.exit(ExitCodes.INPUT_ERROR)
                        i += 2
                    case "v":
                        self.verbose = True
                        i += 1
                    case "verbose":
                        self.verbose = True
                        i += 1
                    case _:
                        self.log_error(f"unknown argument: {args[i]}")
                        sys.exit(ExitCodes.PARSING_ERROR)
                continue
            if action := self.manager.get(args[i]):
                inverted = arg.endswith(FILTER_INVERT_SUFFIX)
                action_cls = action.cls
                action_args = args[i + 1]
                if action_args == "--help":
                    print(action.get_help_long())
                    sys.exit(ExitCodes.SUCCESS)
                action_obj = action_cls.parse(
                    action_args, **{"invert": inverted} if inverted else {}
                )
                actions.append(action_obj)
                i += 2
                continue
            if not arg.startswith(FLAG_PREFIX_LONG) and not arg.startswith(FLAG_PREFIX_SHORT):
                self.items.append(arg)
                i += 1
            else:
                self.log_error(f"unknown argument: {args[i]}")
                sys.exit(ExitCodes.PARSING_ERROR)

        return actions

    def _process_items(self, items: list[Item], actions: list[Action]):
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

    def _create_pipeline(self, actions: list[Action]):
        return self.pipeline_cls(actions=actions, verbose=self.verbose)

    def _print_results(self, items: ItemsContainer):
        if self.mode == "kept":
            for item in items.kept:
                print(item)
        else:
            for item in items.discarded:
                print(item)

    def collect_items(self, items: list[str]) -> list[Item]:
        raise NotImplementedError

    def run(self):
        try:
            actions = self.parse_args()
        except Exception as e:
            self.log_error(f"error while parsing arguments: {e}")
            sys.exit(ExitCodes.PARSING_ERROR)

        if self.read_from_stdin:
            self.items.extend(read_stdin())

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
            sys.exit(ExitCodes.PARSING_ERROR)
        if self.print_results:
            self._print_results(processed_items)
        sys.exit(ExitCodes.SUCCESS)


__all__ = ["PyPipelineCLI"]
