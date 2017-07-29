"""Module to assist with interacting with problems on this Judge."""
from os import listdir
from os.path import isfile, join


def get_available_problems(config):
    """Gets available problems on this Judge.

    :param config: The config for the judge system
    :type config: dict

    :return: List of the available UVa problem numbers
    :rtype: list
    """
    p_dir = config.get('problem_directory')

    # remove the .yaml off the file names
    files = [f[:-5] for f in listdir(p_dir) if isfile(join(p_dir, f))]
    return files
