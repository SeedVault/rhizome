"""Unit tests for module bbot.config"""
import pytest
from tests.bbot.conftest import get_configuration_path
from bbot.config import load_configuration


def test_invalid_env_var():
    """Invalid env_var"""
    with pytest.raises(RuntimeError):
        _ = load_configuration(get_configuration_path(), "IT_DESNT_EXIST")


def test_configuration_file_not_found():
    """Configuration file not found"""
    missing_path = get_configuration_path() + "/it_doesnt_exist"
    with pytest.raises(FileNotFoundError):
        _ = load_configuration(missing_path, "BBOT_ENV")


def test_load_configuration_file_successfully():
    """Load configuration file successfully"""
    settings = load_configuration(get_configuration_path(), "BBOT_ENV",
                                  "testing")
    assert settings  # empty dictionaries evaluate to False in Python
