import argparse
import flask
import glob
import importlib
import logging
import os
import sys
import yaml
import waitress

from datetime import datetime
from extended_uva_judge import logging_helper
from extended_uva_judge.objects import ProblemWorkerFactory
from os.path import basename, isfile, abspath, join

CURRENT_DIR = abspath(__file__).replace('server.pyc', 'server.py').replace(
    'server.py', '')


def register_blueprints(app):
    modules = glob.glob(CURRENT_DIR + 'controllers/*.py')
    raw_mods = [basename(f)[:-3] for f in modules if isfile(f)]

    for mod in raw_mods:
        m = importlib.import_module('extended_uva_judge.controllers.' + mod)
        if hasattr(m, 'mod'):
            app.register_blueprint(m.mod)


def build_app(override_config=None):
    app = flask.Flask('Extended-UVA-Judge',
                      template_folder='templates',
                      static_folder='static')
    config = yaml.load(open(CURRENT_DIR + 'config.yml'))

    if override_config:
        # TODO: Find a better way to merge these. If data exists in the default
        # config but not in the override config (ex: language.FOO.restricted)
        # the default data gets blanked out.
        cfg = yaml.load(open(override_config))
        config.update(cfg)

    logging_helper.initialize(config, app)
    ProblemWorkerFactory.initialize(config)

    register_blueprints(app)

    app.app_config = config

    return app, config


def start_server(override_config=None):
    start = datetime.now()
    app, config = build_app(override_config)
    end = datetime.now()

    logging.getLogger().info('Application built in {time}.'.format(
        time=(end - start)))

    host = config.get('flask', {}).get('host', '0.0.0.0')
    port = config.get('flask', {}).get('port', 8000)
    if config.get('flask', {}).get('debug', False):
        app.run(host=host,
                port=port,
                debug=True)
    else:
        waitress.serve(app,
                       host=host,
                       port=port)


def build_args_parse():
    parser = argparse.ArgumentParser(description='Extended UVa Judge')
    parser.add_argument(
        '--config', action='store', default=None, type=str,
        help='The path to user defined overrides of the config.'
    )
    return parser.parse_args()


def main():
    here_path = abspath(join(CURRENT_DIR, os.pardir))
    if here_path not in sys.path:
        sys.path.append(here_path)
    env_var_override_conf = os.environ.get('EXTENDED_UVA_JUDGE_CONFIG', None)
    arg_parser = build_args_parse()
    start_server(arg_parser.config or env_var_override_conf)


if __name__ == '__main__':
    main()
