import os
import yaml
from extended_uva_judge import errors


def get_problem_directory(app_config):
    """Gets the directory containing the problem configs.

    :return: The path to the problem configs.
    :rtype: str
    """
    problem_directory = app_config['problem_directory']

    if not problem_directory:
        raise errors.MissingConfigEntryError('problem_directory')

    # Check for full windows or *nix directory path
    if not (problem_directory.startswith('/') or ':' in problem_directory):
        # assume it's relative to the current working directory
        problem_directory = os.path.join(os.getcwd(), problem_directory)

    return problem_directory


def get_problem_config(app_config, problem_id):
    """Gets the configuration for this objects corresponding problem.

    :return: The configuration for the users selected problem
    :rtype: dict
    """
    problem_directory = get_problem_directory(app_config)

    problem_config_path = os.path.join(
        problem_directory, '%s.yaml' % problem_id)
    problem_config = yaml.load(open(problem_config_path))

    return problem_config


def does_problem_config_exist(app_config, problem_id):
    """Checks to see if the problem configuration exists in the system.

    :return: True if it exists, false otherwise
    :rtype: bool
    """
    problem_directory = get_problem_directory(app_config)

    problem_config_path = os.path.join(
        problem_directory, '%s.yaml' % problem_id)

    return os.path.exists(problem_config_path)
