"""Module to assist with configuring logging"""
import os.path as path
import logging

from logging.handlers import RotatingFileHandler
from logging import StreamHandler

# https://docs.python.org/2/library/logging.html#logrecord-attributes
DEFAULT_LOG_MAX_BYTES = 1024 * 1024
DEFAULT_LOG_MESSAGE_FORMAT = ('%(asctime)s - %(process)s - %(thread)s - '
                              '%(levelname)s - %(module)s - %(funcName)s - '
                              '%(lineno)s - %(message)s')
DEFAULT_LOG_FILE_COUNT = 3
DEFAULT_LOG_FILE_PATH = ''
DEFAULT_LOG_FILE_NAME = 'log'
DEFAULT_LOG_TYPE = 'console'
DEFAULT_LOG_LEVEL = 'NOTSET'
INITIALIZED = False


def initialize(config, flask_app=None):
    """Initializes the logging helper and loggers

    :param config: the configuration to use for logging.
    :type config: dict
    :param flask_app: the flask application to associate loggers to.
    :type flask_app: flask.Flask
    """
    global INITIALIZED
    if INITIALIZED:
        return

    if isinstance(config, dict):
        settings = _get_settings_from_dict(config)
    else:
        settings = {}

    if 'type' not in settings:
        INITIALIZED = True
        return

    # Build the logging formatter
    formatter = logging.Formatter(settings['message_format'])

    for log_type in settings['type'].split(';'):
        if log_type == 'rolling':
            logger = logging.getLogger()
            logger.setLevel(settings['level'])
            _setup_rolling_log(flask_app, formatter, settings)
        else:
            logger = logging.getLogger()
            logger.setLevel(settings['level'])
            _setup_console_log(flask_app, formatter)

    INITIALIZED = True


def _setup_console_log(flask_app, formatter):
    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.NOTSET)
    stream_handler.setFormatter(formatter)
    _add_flask_logging_handler(flask_app, stream_handler)


def _setup_rolling_log(flask_app, formatter, settings):
    log_file_count = settings['file_count']
    log_file_path = settings['file_path']
    log_max_file_bytes = settings['max_file_bytes']
    log_file_name = settings['file_name']
    log_level = settings['level']

    # Configure default rotating handler
    log_rotating_handler = RotatingFileHandler(
        filename=path.join(log_file_path, log_file_name + '.log'),
        backupCount=log_file_count,
        maxBytes=log_max_file_bytes)
    log_rotating_handler.setLevel(log_level)
    log_rotating_handler.setFormatter(formatter)
    _add_flask_logging_handler(flask_app, log_rotating_handler)

    # Configure error specific rotating handler
    err_rotating_handler = RotatingFileHandler(
        filename=path.join(log_file_path, log_file_name + '.err.log'),
        backupCount=log_file_count,
        maxBytes=log_max_file_bytes)
    err_rotating_handler.setLevel(logging.ERROR)
    err_rotating_handler.setFormatter(formatter)
    _add_flask_logging_handler(flask_app, err_rotating_handler)


def _add_flask_logging_handler(app, handler, logger_name=None):
    if app is not None:
        app.logger.addHandler(handler)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)


def _get_settings_from_dict(in_config):
    if 'logging' not in in_config:
        return {}

    config = in_config['logging']

    # Get the values from our config, if they exist
    log_file_name = (
        DEFAULT_LOG_FILE_NAME
        if 'file_name' not in config or not config['file_name']
        else config['file_name'])
    log_file_path = (
        DEFAULT_LOG_FILE_PATH
        if 'file_path' not in config or not config['file_path']
        else config['file_path'])
    log_message_format = (
        DEFAULT_LOG_MESSAGE_FORMAT
        if 'message_format' not in config or not config[
            'message_format']
        else config['message_format'])
    log_file_count = (
        DEFAULT_LOG_FILE_COUNT
        if 'file_count' not in config or not config['file_count']
        else config['file_count'])
    log_max_file_bytes = (
        DEFAULT_LOG_MAX_BYTES
        if 'max_file_bytes' not in config or not config[
            'max_file_bytes']
        else config['max_file_bytes'])
    log_type = (
        DEFAULT_LOG_TYPE
        if 'type' not in config or not ['type']
        else str(config['type']).lower()
    )
    log_level = (
        DEFAULT_LOG_LEVEL
        if 'level' not in config or not ['level']
        else str(config['level']).upper()
    )

    return {
        'type': log_type,
        'file_name': log_file_name,
        'file_path': log_file_path,
        'message_format': log_message_format,
        'file_count': log_file_count,
        'max_file_bytes': log_max_file_bytes,
        'level': log_level
    }
