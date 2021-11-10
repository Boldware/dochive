"""
Standalone file utils.
Nothing in this module should have knowledge of config or the layout
and structure of the site and pages in the site.
"""


import logging
import os
import shutil
import re
import yaml
import fnmatch
import posixpath
import functools
import importlib_metadata
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse
from yaml_env_tag import construct_env_tag

from mkdocs import exceptions

log = logging.getLogger(__name__)

markdown_extensions = [
    '.markdown',
    '.mdown',
    '.mkdn',
    '.mkd',
    '.md'
]


def yaml_load(source, loader=yaml.Loader):
    """
    Wrap PyYaml's loader so we can extend it to suit our needs.
    Load all strings as unicode.
    https://stackoverflow.com/a/2967461/3609487
    """

    def construct_yaml_str(self, node):
        """
        Override the default string handling function to always return
        unicode objects.
        """
        return self.construct_scalar(node)

    class Loader(loader):
        """
        Define a custom loader derived from the global loader to leave the
        global loader unaltered.
        """

    # Attach our unicode constructor to our custom loader ensuring all strings
    # will be unicode on translation.
    Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)

    # Attach Environment Variable constructor.
    # See https://github.com/waylan/pyyaml-env-tag
    Loader.add_constructor('!ENV', construct_env_tag)

    try:
        return yaml.load(source, Loader)
    finally:
        # TODO: Remove this when external calls are properly cleaning up file
        # objects. Some mkdocs internal calls, sometimes in test lib, will
        # load configs with a file object but never close it.  On some
        # systems, if a delete action is performed on that file without Python
        # closing that object, there will be an access error. This will
        # process the file and close it as there should be no more use for the
        # file once we process the yaml content.
        if hasattr(source, 'close'):
            source.close()


def copy_file(source_path, output_path):
    """
    Copy source_path to output_path, making sure any parent directories exist.
    The output_path may be a directory.
    """
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, os.path.basename(source_path))
    shutil.copyfile(source_path, output_path)

def yaml_write_file(content, output_path):
    """
    Convert content to YAML and Write to output_path, making sure any parent directories exist.
    """
    write_file(yaml.dump(content, sort_keys=False).encode(), output_path)
    
def write_file(content, output_path):
    """
    Write content to output_path, making sure any parent directories exist.
    """
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(content)


def clean_directory(directory):
    """
    Remove the content of a directory recursively but not the directory itself.
    """
    if not os.path.exists(directory):
        return

    for entry in os.listdir(directory):

        # Don't remove hidden files from the directory. We never copy files
        # that are hidden, so we shouldn't delete them either.
        if entry.startswith('.'):
            continue

        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            shutil.rmtree(path, True)
        else:
            os.unlink(path)

def is_markdown_file(path):
    """
    Return True if the given file path is a Markdown file.
    https://superuser.com/questions/249436/file-extension-for-markdown-files
    """
    return any(fnmatch.fnmatch(path.lower(), f'*{x}') for x in markdown_extensions)

class CountHandler(logging.NullHandler):
    """ Counts all logged messages >= level. """

    def __init__(self, **kwargs):
        self.counts = defaultdict(int)
        super().__init__(**kwargs)

    def handle(self, record):
        rv = self.filter(record)
        if rv:
            # Use levelno for keys so they can be sorted later
            self.counts[record.levelno] += 1
        return rv

    def get_counts(self):
        return [(logging.getLevelName(k), v) for k, v in sorted(self.counts.items(), reverse=True)]


# A global instance to use throughout package
log_counter = CountHandler()

# For backward compatability as some plugins import it.
# It is no longer nessecary as all messages on the
# `mkdocs` logger get counted automaticaly.
warning_filter = logging.Filter()