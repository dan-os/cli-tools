import enum
from dataclasses import dataclass
from typing import Optional

import pytest

from codemagic.apple.app_store_connect.resource_manager import ResourceManager

StubEnum = enum.Enum('StubEnum', {'A': 'a', 'B': 'b'})


class CustomString(str):
    ...


@dataclass
class StubFilter(ResourceManager.Filter):
    field_one: Optional[str] = None
    field_two: Optional[StubEnum] = None
    field_three_four: Optional[CustomString] = None
    field_with__dot__dots: Optional[str] = None


@pytest.mark.parametrize('filter_params, expected_query_params', [
    ({'field_one': '1'}, {'filter[fieldOne]': '1'}),
    ({'field_two': StubEnum.A}, {'filter[fieldTwo]': 'a'}),
    ({'field_three_four': CustomString('34')}, {'filter[fieldThreeFour]': '34'}),
    ({'field_one': '1', 'field_two': None}, {'filter[fieldOne]': '1'}),
    ({'field_two': StubEnum.B, 'field_one': None}, {'filter[fieldTwo]': 'b'}),
    ({'field_three_four': CustomString('34'), 'field_one': None, 'field_two': None}, {'filter[fieldThreeFour]': '34'}),
    ({'field_one': '1', 'field_two': StubEnum.A}, {'filter[fieldOne]': '1', 'filter[fieldTwo]': 'a'}),
    ({'field_with__dot__dots': 'value'}, {'filter[fieldWith.dots]': 'value'}),
])
def test_resource_manager_filter_to_params_conversion(filter_params, expected_query_params):
    test_filter = StubFilter(**filter_params)
    assert test_filter.as_query_params() == expected_query_params


@pytest.mark.parametrize('snake_case_input, expected_camel_case_output', [
    ('', ''),
    ('word', 'word'),
    ('_word', 'Word'),
    ('snake_case', 'snakeCase'),
    ('snake_case_', 'snakeCase_'),
    ('snake_case_ snakeCase', 'snakeCase_ snakeCase'),
    ('a_b_c_d_e_f', 'aBCDEF'),
])
def test_resource_manager_filter_camel_case_converter(snake_case_input, expected_camel_case_output):
    converted_input = ResourceManager.Filter._snake_to_camel(snake_case_input)
    assert converted_input == expected_camel_case_output


@pytest.mark.parametrize('dot_input, expected_dot_output', [
    ('', ''),
    ('no_dots', 'no_dots'),
    ('my_resource__dot__field', 'my_resource.field'),
    ('two__dot__dots__dot__field', 'two.dots.field'),
])
def test_resource_manager_filter_dots(dot_input, expected_dot_output):
    converted_input = ResourceManager.Filter._handle_dots(dot_input)
    assert converted_input == expected_dot_output
