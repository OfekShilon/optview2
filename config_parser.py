import yaml
import re

def parse(f):
    "Parse config file"
    # TODO - add scheme; currently we just take whatever there.
    config = yaml.safe_load(f)
    if config.get('use_remark_filters', True) and 'remark_filters' in config and len(config['remark_filters']) > 0:
        # config wants a single regex, transform to a single expression
        try:
            regexes = [re.compile(x) for x in config['remark_filters']]
        except Exception as ex:
            raise Exception(f"Failed to parse regex in remarks_filters config. Details {ex}")
        config['remark_filter'] = '|'.join(x.pattern for x in regexes) 

    return config
