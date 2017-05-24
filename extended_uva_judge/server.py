import flask
import glob
import importlib
import logging
import os
import yaml
import waitress

from datetime import datetime
from extended_uva_judge import logging_helper
from os.path import dirname, basename, isfile


def register_blueprints(app):
    modules = glob.glob(dirname(__file__) + '/controllers/*.py')
    raw_mods = [basename(f)[:-3] for f in modules if isfile(f)]

    for mod in raw_mods:
        m = importlib.import_module('controllers.' + mod)
        if hasattr(m, 'mod'):
            app.register_blueprint(m.mod)


def build_app():
    app = flask.Flask('Extended-UVA-Judge',
                      template_folder='templates',
                      static_folder='static')
    config = yaml.load(open('config.yml'))

    override_conf = os.environ.get('EXTENDED_UVA_JUDGE_CONFIG', None)
    if override_conf:
        # TODO: Find a better way to merge these. If data exists in the default
        # config but not in the override config (ex: language.FOO.restricted)
        # the default data gets blanked out.
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


def main():
    start_server()


if __name__ == '__main__':
    start_server()
