#!/usr/bin/env python3
from __future__ import annotations

import argparse
import enum
import os
import types
import typing


class ActionCallable:
    def __call__(self, *args, **kwargs):
        pass

    is_cli_action: bool
    action_name: str
    required_arguments: typing.Sequence[Argument]


class EnumArgumentValue(enum.Enum):

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.name.lower()


class EnvironmentArgumentValue:

    def __init__(self, raw_value: str):
        self._raw_value = raw_value
        self.value = self._parse_value()

    @classmethod
    def _is_valid(cls, value: str) -> bool:
        return bool(value)

    def _is_from_environment(self) -> bool:
        return self._raw_value.startswith('@env:')

    def _get_from_environment(self) -> str:
        key = self._raw_value[5:]
        try:
            return os.environ[key]
        except KeyError:
            raise argparse.ArgumentTypeError(f'Environment variable "{key}" is not defined')

    def _parse_value(self) -> str:
        if self._is_from_environment():
            value = self._get_from_environment()
        else:
            value = self._raw_value
        if not self._is_valid(value):
            raise argparse.ArgumentTypeError('Provided value is not valid')
        return value

    @classmethod
    def get_description(cls, properties: ArgumentProperties) -> str:
        description = f'{properties.description.rstrip(".")}.'
        usage = f'Alternatively to entering "<{properties.key}>" in plaintext, ' \
            f'it may also be specified using a "@env:" prefix followed by a environment variable name.'
        example = 'Example: "@env:<variable>" uses the value in the environment variable named "<variable>".'
        return '\n'.join([description, usage, example])

    def __str__(self):
        return self._raw_value

    def __repr__(self):
        return self._raw_value


class ArgumentProperties(typing.NamedTuple):
    key: str
    description: str
    type: typing.Union[typing.Type, typing.Callable[[str], typing.Any]] = str
    flags: typing.Tuple[str, ...] = tuple()
    argparse_kwargs: typing.Optional[typing.Dict[str, object]] = None
    is_action_kwarg: bool = False

    def get_description(self):
        description = self.description
        default = (self.argparse_kwargs or {}).get('default', None)
        if default is not None:
            description = f'{description} [Default: {default}]'

        if isinstance(self.type, (types.FunctionType, types.MethodType)):
            return description
        elif issubclass(self.type, EnvironmentArgumentValue):
            return self.type.get_description(self)
        else:
            return description


class Argument(ArgumentProperties, enum.Enum):

    def register(self, argument_group: argparse._ArgumentGroup):
        argument_group.add_argument(
            *self.value.flags,
            type=self.value.type,
            help=self.value.get_description(),
            dest=self.value.key,
            **(self.value.argparse_kwargs or {}))

    def is_required(self):
        return (self.value.argparse_kwargs or {}).get('required', True)

    def get_default(self):
        return (self.value.argparse_kwargs or {}).get('default', None)

    @classmethod
    def get_action_kwargs(cls, cli_action: ActionCallable, cli_args: argparse.Namespace) -> typing.Dict[str, object]:
        return {
            arg_type.value.key: getattr(cli_args, arg_type.value.key, arg_type.get_default())
            for arg_type in cli_action.required_arguments
            if arg_type.value.is_action_kwarg
        }
