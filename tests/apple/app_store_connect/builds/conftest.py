import json
import pathlib
from typing import Dict

import pytest


_RESOURCE_MOCKS_DIR = pathlib.Path(__file__).parent.parent.parent / 'resources' / 'mocks'


class MockResponse:
    def __init__(self, mock_data):
        self.data = {'data': mock_data}

    def json(self):
        return self.data


@pytest.fixture
def build_response() -> MockResponse:
    mock_path = _RESOURCE_MOCKS_DIR / 'build.json'
    mock_data = json.loads(mock_path.read_text())
    return MockResponse(mock_data)
