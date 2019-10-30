#!/usr/bin/env python3

from __future__ import annotations

import abc
import argparse
import logging
import os
import shlex
import sys
from functools import wraps
from itertools import chain
from typing import Optional, Sequence, Iterable, Type, List

from .argument import Argument, ActionCallable
from .cli_process import CliProcess
from .cli_types import CommandArg, ObfuscatedCommand


class CliAppException(Exception):

    def __init__(self, cli_process: CliProcess, message: str):
        self.cli_process = cli_process
        self.message = message

    def __str__(self):
        return f'Running {self.cli_process.safe_form} failed with exit code {self.cli_process.returncode}: {self.message}'


class CliApp(metaclass=abc.ABCMeta):
    CLI_EXCEPTION_TYPE: Type[CliAppException] = CliAppException

    def __init__(self, dry=False):
        self.dry_run = dry
        self.default_obfuscation = []
        self.obfuscation = 8 * '*'
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def from_cli_args(cls, cli_args: argparse.Namespace):
        return cls()

    @classmethod
    def _handle_cli_exception(cls, cli_exception: CliAppException):
        sys.stderr.write(f'{cli_exception.message}\n')
        sys.exit(cli_exception.cli_process.returncode)

    @classmethod
    def invoke_cli(cls):
        args = CliApp.setup_cli(cls)
        instance = cls.from_cli_args(args)
        cli_action = {ac.action_name: ac for ac in instance.get_cli_actions()}[args.action]
        try:
            return cli_action(**Argument.get_action_kwargs(cli_action, args))
        except cls.CLI_EXCEPTION_TYPE as cli_exception:
            cls._handle_cli_exception(cli_exception)

    @classmethod
    def get_class_cli_actions(cls) -> Iterable[ActionCallable]:
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and getattr(attr, 'is_cli_action', False):
                yield attr

    def get_cli_actions(self) -> Iterable[ActionCallable]:
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and getattr(attr, 'is_cli_action', False):
                yield attr

    @classmethod
    def _setup_logging(cls, cli_args: argparse.Namespace):
        if not cli_args.log_commands:
            return

        stream = {'stderr': sys.stderr, 'stdout': sys.stdout}[cli_args.log_stream]
        log_level = logging.DEBUG if cli_args.verbose else logging.INFO
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s > %(message)s', '%m-%d %H:%M:%S')

        handler = logging.StreamHandler(stream)
        handler.setLevel(log_level)
        handler.setFormatter(formatter)

        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(log_level)

    @classmethod
    def _setup_default_cli_options(cls, action_parser):
        action_parser.add_argument('--disable-logging', dest='log_commands', action='store_false',
                                   help='Disable log output for actions')
        action_parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Enable verbose logging')
        action_parser.add_argument('--log-stream', type=str, default='stderr', choices=['stderr', 'stdout'],
                                   help='Choose which stream to use for log output. (Default: stderr)')
        action_parser.set_defaults(verbose=False, log_commands=True)

    @classmethod
    def setup_cli(cls, command_executor_type: Type[CliApp]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=command_executor_type.__doc__)

        action_parsers = parser.add_subparsers(dest='action')
        for sub_action in command_executor_type.get_class_cli_actions():
            action_parser = action_parsers.add_parser(
                sub_action.action_name,
                help=sub_action.__doc__,
                description=sub_action.__doc__)

            cls._setup_default_cli_options(action_parser)
            required_arguments = action_parser.add_argument_group(f'required arguments for "{sub_action.action_name}"')
            optional_arguments = action_parser.add_argument_group(f'optional arguments for "{sub_action.action_name}"')
            for argument in sub_action.required_arguments:
                argument_group = required_arguments if argument.is_required() else optional_arguments
                argument.register(argument_group)
        args = parser.parse_args()
        cls._setup_logging(args)

        if not args.action:
            parser.print_help()
            sys.exit(0)

        return args

    def _obfuscate_command(self, command_args: Sequence[CommandArg],
                           obfuscate_args: Optional[Iterable[CommandArg]] = None) -> ObfuscatedCommand:
        # TODO: support regex expressions for matching
        obfuscate_args = set(chain((obfuscate_args or []), self.default_obfuscation))
        obfuscated = ' '.join(
            self.obfuscation if arg in obfuscate_args else shlex.quote(str(arg))
            for arg in command_args)
        return ObfuscatedCommand(obfuscated)

    @classmethod
    def _expand_variables(cls, command_args: Sequence[CommandArg]) -> List[str]:
        def expand(command_arg: CommandArg):
            expanded = os.path.expanduser(os.path.expandvars(command_arg))
            if isinstance(expanded, bytes):
                return expanded.decode()
            return expanded

        return [expand(command_arg) for command_arg in command_args]

    def execute(self, command_args: Sequence[CommandArg],
                obfuscate_args: Optional[Sequence[CommandArg]] = None,
                show_output: bool = True) -> CliProcess:
        return CliProcess(
            command_args,
            self._obfuscate_command(command_args, obfuscate_args),
            dry=self.dry_run,
            print_streams=show_output
        ).execute()


def action(action_name: str, *arguments: Argument, optional_arguments=tuple()):
    """
    Decorator to mark that the method is usable form CLI
    :param action_name: Name of the CLI parameter
    :param arguments: CLI arguments that are required for this method to work
    :param optional_arguments: CLI arguments that can be omitted
    """

    def decorator(func):
        if func.__doc__ is None:
            raise RuntimeError(f'Action "{action_name}" defined by {func} is not documented')
        func.is_cli_action = True
        func.action_name = action_name
        func.required_arguments = arguments
        func.optionals = optional_arguments

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
