import flask
import glob
import importlib
import logging
import logging_helper
import os
import yaml
import waitress

from datetime import datetime
from os.path import dirname, basename, isfile


def register_blueprints(app):
    modules = glob.glob(dirname(__file__) + '/controllers/*.py')
    raw_mods = [basename(f)[:-3] for f in modules if isfile(f)]
    mods = [m for m in raw_mods if not m.startswith('__')]

    for mod in mods:
        m = importlib.import_module('controllers.' + mod)
        app.register_blueprint(m.mod)


def build_app():
    app = flask.Flask('Extended-UVA-Judge',
                      template_folder='templates',
                      static_folder='static')
    config = yaml.load(open('config.yml'))

    override_conf = os.environ.get('EXTENDED_UVA_JUDGE_CONFIG', None)
    if override_conf:
        cfg = yaml.load(open(override_conf))
        config.update(cfg)

    logging_helper.initialize(config, app)

    register_blueprints(app)

    app.app_config = config

    return app, config


def start_server():
    start = datetime.now()
    app, config = build_app()
    end = datetime.now()

    logging.getLogger().debug('Application built in %s.' % (end - start))

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


if __name__ == '__main__':
    start_server()
