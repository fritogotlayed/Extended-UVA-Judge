from os import listdir
from os.path import isfile, join


def get_available_problems(config):
    p_dir = config.get('problem_directory')
    # remove the .yaml off the file names
    files = [f[:-5] for f in listdir(p_dir) if isfile(join(p_dir, f))]
    return files
