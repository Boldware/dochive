## References https://github.com/mkdocs/mkdocs/blob/d9b957e771bd6380ba5c865b5991b402ac3e1382/mkdocs/commands/serve.py 

import logging
import re

from shutil import Error

from jinja2.exceptions import TemplateNotFound
import jinja2

from datetime import date
from os.path import isdir, isfile, join, abspath
from os import walk
from pathlib import Path

from dochive.config import load_config, load_config_str
from dochive import utils

log = logging.getLogger(__name__)

def digest(template=None, limit=None, input_dir=None, output_file=None, **kwargs):
    """
    Create the digest page for a given collection of documents
    
    Accepts a directory of documents with metadata and limits to populate a Jinja template and stores the 
    resulting .md file in a supplied directory
    """

    def builder():
        log.info("Building digest...")
        pBlogs = r'\d{4}-\d{2}-\d{2}'
        print(next(walk(input_dir)))
        root, dirs, files = next(walk(input_dir))
        recent_files = [join(root, file) for file in files if re.match(pBlogs, file)]
        recent_files.sort(reverse=True)
        
        pMetaData = r'---(.+?)---'
        configs = []
        l = limit if len(recent_files)>limit else len(recent_files)
        for file in recent_files[:limit]:
            with open(file, 'r') as f:
                metadata = re.match(pMetaData, f.read(), re.DOTALL).group(1)
                configs.append(load_config_str(metadata))
        return {'configs': configs}

    def generate_digest(template, configs, output_file):
        with open(abspath(template), 'r', encoding='utf-8', errors='strict') as f:
            template = jinja2.Template(f.read())
            blog = template.render(configs)
            if blog.strip():
                utils.write_file(blog.encode('utf-8'), output_file)
            else:
                log.info(f"Template skipped: '{template}' generated empty output.")
        
    try:
        # Perform the initial build
        # read metadata from files in provided path
        configs = builder()        
        
        generate_digest(template, configs, output_file)
        
    # except Exception as e:
    #     log.warning(f"Error reading template '{template}': {e}")    
    except Error as e:
        print(e)
