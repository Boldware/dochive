## References https://github.com/mkdocs/mkdocs/blob/d9b957e771bd6380ba5c865b5991b402ac3e1382/mkdocs/commands/serve.py 

import logging

from slugify import slugify
from shutil import Error

from jinja2.exceptions import TemplateNotFound
import jinja2

from datetime import date, datetime
from os.path import isdir, isfile, join, abspath
from pathlib import Path

from dochive.config import load_config
from dochive import utils

log = logging.getLogger(__name__)

def add(templates=None, config_file=None, configs=None, nav=None, timestamp=None, output_dir=None, mkdocs_file=None, **kwargs):
    """
    Create the directory structure and templates for a new document entry
    
    Accepts a yaml config to populate a Jinja template and stores the resulting
    .md file in a directory according to the timestamp parameter
    """

    def builder():
        log.info("Building archive...")
        config = load_config(
            config_file=config_file,
        )
        if configs:
            addition = dict(list(map(lambda elem: tuple(elem.split(':',1)), configs)))
            config = {**config, **addition}
        return config

    # add new document to mkdocs config
    def update_archive(config, publish_date: date, entry):
        try: ####### TODO: Update to use the nav parameter
            config["nav"][2]["Blogs"][1][publish_date.year].insert(0, entry)
        except IndexError as e:
            log.debug(f"Adding new year to mkdocs.yml")
            config["nav"][2]["Blogs"].insert(1, {publish_date.year:[entry]})
        config.write_file()

    def generate_document(template_file, config, dest_file):
        with open(abspath(template_file), 'r', encoding='utf-8', errors='strict') as f:
            template = jinja2.Template(f.read())
            doc = template.render(config)
            if doc.strip():
                utils.write_file(doc.encode('utf-8'), dest_file)
            else:
                log.info(f"Template skipped: '{template_file}' generated empty output.")
        
    try:
        # Perform the initial build
        # build the .md file and write to blog directory
        config = builder()
        
        if timestamp is None:        
            config['publish_date'] = date.today()
        else:
            config['publish_date'] = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")

        template_file = f"{templates}/blog-post-{config['type']}.md.j2"
        blog_filename = f"{config['publish_date']:%Y-%m-%d}-{slugify(config['title'])}.md"
        config['filename'] = blog_filename
        dest_file = f"{output_dir}/{blog_filename}"
        
        generate_document(template_file, config, dest_file)

        # get the relative path from within the docs directory
        p = Path(dest_file)
        entry = Path(*p.parts[2:]) 

        # Update the mkdocs.yml file nav with the new structure
        mkdocs_config = load_config(config_file=mkdocs_file)
        update_archive(mkdocs_config, config['publish_date'], {config['title']: str(entry)})
        
    except Exception as e:
        log.warning(f"Error reading template '{template_file}': {e}")    
    except Error as e:
        print(e)
