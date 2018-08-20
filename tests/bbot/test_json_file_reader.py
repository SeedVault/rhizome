"""Unit tests for module bbot.json_file_reader"""
import os
import pytest
from bbot.json_file_reader import JsonFileReader

def test_configuration_file_not_found():
    """Configuration file not found"""
    reader = JsonFileReader({})
    reader.filename = 'it_doesnt_exist.json'
    reader = JsonFileReader({})
    with pytest.raises(FileNotFoundError):
        _ = reader.read()


def test_read_configuration_file():
    """Configuration file not found"""
    reader = JsonFileReader({})
    reader.filename = os.path.abspath(os.path.dirname(__file__)
                                      + "/test_json_file_reader.json")
    settings = reader.read()
    assert settings['bot']['name'] == "Example"
