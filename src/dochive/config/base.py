import logging
import os
import sys
from yaml import YAMLError
from collections import UserDict

from dochive import exceptions, utils

log = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised during the validation process of the config on errors."""

class Config(UserDict):
    """
    DocHive Configuration dict
    This is a fairly simple extension of a standard dictionary.
    """

    def __init__(self, config_file_path=None):
        """
        The schema is a Python dict which maps the config name to a validator.
        """

        # Ensure config_file_path is a Unicode string
        if config_file_path is not None and not isinstance(config_file_path, str):
            try:
                # Assume config_file_path is encoded with the file system encoding.
                config_file_path = config_file_path.decode(encoding=sys.getfilesystemencoding())
            except UnicodeDecodeError:
                raise ValidationError("config_file_path is not a Unicode string.")
        self.config_file_path = config_file_path
        self.data = {}

        self.user_configs = []

    def load_dict(self, patch):

        if not isinstance(patch, dict):
            raise exceptions.ConfigurationError(
                "The configuration is invalid. The expected type was a key "
                "value mapping (a python dict) but we got an object of type: "
                "{}".format(type(patch)))

        self.user_configs.append(patch)
        self.data.update(patch)

    def load_file(self, config_file):
        try:
            return self.load_dict(utils.yaml_load(config_file))
        except YAMLError as e:
            raise exceptions.ConfigurationError(
                f"DocHive encountered an error parsing the configuration file: {e}"
            )

    def write_file(self):
        f = self.pop("config_file_path")
        utils.yaml_write_file(self.data, f)

def _open_config_file(config_file):

    # Default to the standard config filename.
    if config_file is None:
        config_file = os.path.abspath('config.yml')

    # If closed file descriptor, get file path to reopen later.
    if hasattr(config_file, 'closed') and config_file.closed:
        config_file = config_file.name

    log.debug(f"Loading configuration file: {config_file}")

    # If it is a string, we can assume it is a path and attempt to open it.
    if isinstance(config_file, str):
        if os.path.exists(config_file):
            config_file = open(config_file, 'rb')
        else:
            raise exceptions.ConfigurationError(
                f"Config file '{config_file}' does not exist.")

    # Ensure file descriptor is at begining
    config_file.seek(0)

    return config_file

def load_config_str(config_str=None, **kwargs):
    """
    Load the configuration from a config string
    Extra kwargs are passed to the configuration to replace any default values
    unless they themselves are None.
    """
    options = kwargs.copy()

    # Filter None values from the options. This usually happens with optional
    # parameters from Click.
    for key, value in options.copy().items():
        if value is None:
            options.pop(key)

    cfg = Config()
    # First load the config file
    cfg.load_file(config_str)
    # Then load the options to overwrite anything in the config.
    cfg.load_dict(options)

    for key, value in cfg.items():
        log.debug(f"Config value: '{key}' = {value!r}")

    return cfg

def load_config(config_file=None, **kwargs):
    """
    Load the configuration for a given file object or name
    The config_file can either be a file object, string or None. If it is None
    the default `config.yml` filename will loaded.
    Extra kwargs are passed to the configuration to replace any default values
    unless they themselves are None.
    """
    options = kwargs.copy()

    # Filter None values from the options. This usually happens with optional
    # parameters from Click.
    for key, value in options.copy().items():
        if value is None:
            options.pop(key)

    config_file = _open_config_file(config_file)
    options['config_file_path'] = getattr(config_file, 'name', '')

    cfg = Config(config_file_path=options['config_file_path'])
    # First load the config file
    cfg.load_file(config_file)
    # Then load the options to overwrite anything in the config.
    cfg.load_dict(options)

    for key, value in cfg.items():
        log.debug(f"Config value: '{key}' = {value!r}")

    return cfg