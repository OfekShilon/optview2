from typing import IO
import yaml
import re


def parse(yaml_config_file: IO):
    "Parse config file"
    # TODO - add scheme; currently we just take whatever is there.
    config = yaml.safe_load(yaml_config_file)
    if config.get('use_remark_filters', True) and 'remark_filters' in config and len(config['remark_filters']) > 0:
        # config wants a single regex, transform to a single expression
        try:
            regexes = [re.compile(x) for x in config['remark_filters']]
        except Exception as ex:
            raise Exception(f"Failed to parse regex in remarks_filters config. Details {ex}")
        config['remark_filter'] = '|'.join(x.pattern for x in regexes)

    return config
