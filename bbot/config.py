"""Manage configuration settings."""
import errno
import os
import re
import yaml
from dotenv import load_dotenv

def load_configuration(config_path: str, var_name: str,
                       environment_name: str = "",) -> dict:
    """
    Retrieve configuration settings for an environment name.

    Load configuration settings from a YAML file and interpolate its content
    with environment variables. If not specified, environment name will be
    autodetected from the environment variable identified by var_name.

    :param config_path: Full path to the configuation files.
    :param var_name: The name of environment variable (e.g.: "BBOT_ENV").
    :param environment_name: Optional environment name (e.g.: "development")
                             to be used instead of the value of 'var_name'
    :raises RuntimeError if environment variable 'var_name' is not defined.
    :raises FileNotFoundError if the configuration file is not found.
    :return: A dictionary of configuration settings.
    """
    if not environment_name:
        if not var_name in os.environ:
            raise RuntimeError(
                f"FATAL ERRR: Missing environment variable {var_name}"
            )
        environment_name = os.environ[var_name]
    else:
        os.environ[var_name] = environment_name

    # Remember the path
    os.environ["BBOT_CONFIG_PATH"] = config_path

    # Load .env file
    env_file = config_path + '/.env_'+ environment_name
    load_dotenv(env_file)
    
    # Load YAML file and interpolate its content with environment variables
    config_file = config_path + "/config_" + environment_name + ".yml"

    pattern = re.compile(r'^\<%= ENV\[\'(.*)\'\] %\>(.*)$')
    yaml.add_implicit_resolver("!env", pattern)
    def env_constructor(loader, node):
        value = loader.construct_scalar(node)
        env_var, remaining_path = pattern.match(value).groups()
        return os.environ[env_var] + remaining_path
    yaml.add_constructor('!env', env_constructor)

    pattern_unquoted = re.compile(r'^\<%= ENV_UNQUOTED\[\'(.*)\'\] %\>(.*)$')
    yaml.add_implicit_resolver("!env_unquoted", pattern_unquoted)
    def env_unquoted_constructor(loader, node):
        value = loader.construct_scalar(node)
        env_var, remaining_path = pattern_unquoted.match(value).groups()
        return eval(os.environ[env_var] # pylint: disable=eval-used
                    + remaining_path)
    yaml.add_constructor('!env_unquoted', env_unquoted_constructor)
    
    with open(config_file, 'r') as ymlfile:
        return yaml.load(ymlfile, Loader=yaml.Loader) # https://github.com/yaml/pyyaml/issues/265
