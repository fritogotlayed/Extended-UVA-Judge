#!/usr/bin/env python
"""Module that is the main entry point of the automated judge

This module handles configuring Flask properly with all the controllers as well
as initializing logging and other support items.
"""
# Built-ins
import argparse
import glob
import importlib
import logging
import os
import os.path as path
import sys

from datetime import datetime

# libs
import flask
import waitress
import yaml

from extended_uva_judge import logging_helper
from extended_uva_judge.objects import ProblemWorkerFactory

CURRENT_DIR = path.abspath(__file__).replace('.pyc', '.py').replace(
    'server.py', '')


def register_blueprints(app):
    """Scans the 'controllers' folder for controller modules

    Scans the "controllers" folder for modules that have a attribute named
    "MOD". These modules are then automatically registered with the flask
    application.

    :param app: The flask application
    """
    modules = glob.glob(CURRENT_DIR + 'controllers/*.py')
    raw_mods = [path.basename(f)[:-3] for f in modules if path.isfile(f)]

    for mod in raw_mods:
        controller = importlib.import_module(
            'extended_uva_judge.controllers.' + mod)
        if hasattr(controller, 'MOD'):
            app.register_blueprint(controller.MOD)


def build_app(override_config=None):
    """Builds the flask application

    :param override_config: Path to configuration to override defaults.
    :type override_config: str

    :return: tuple of the flask application and configuration dictionary
    :rtype: tuple
    """
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
    """Launches the Judge

    :param override_config: Path to configuration to override the defaults
    :type override_config: str
    """
    start = datetime.now()
    app, config = build_app(override_config)
    end = datetime.now()

    time = end - start
    logging.getLogger().info('Application built in %s.', time)

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
    """Build the arg_parse object

    Builds the arg_parse object to assist with parsing command line provided
    arguments.

    :return: arg parse object
    """
    parser = argparse.ArgumentParser(description='Extended UVa Judge')
    parser.add_argument(
        '--config', action='store', default=None, type=str,
        help='The path to user defined overrides of the config.'
    )
    return parser.parse_args()


def main():
    """Main entry point for this module when it is run directly

    :return:
    """
    here_path = path.abspath(path.join(CURRENT_DIR, os.pardir))
    if here_path not in sys.path:
        sys.path.append(here_path)
    env_var_override_conf = os.environ.get('EXTENDED_UVA_JUDGE_CONFIG', None)
    arg_parser = build_args_parse()
    start_server(arg_parser.config or env_var_override_conf)


if __name__ == '__main__':
    main()
