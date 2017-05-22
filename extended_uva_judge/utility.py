from extended_uva_judge import errors
from subprocess32 import STDOUT, check_output
from random import choice
from string import ascii_letters

import os
import shutil
import yaml
import logging

_lang_map = {
    'python': 'python2',
    'python2': 'python2',
    'py2': 'python2',
    'python3': 'python3',
    'py3': 'python3'
}


class ProblemWorker:
    def __init__(self, lang, problem_id, config):
        self.lang = lang
        self.problem_id = problem_id
        self.config = config  # type: dict
        self.log = logging.getLogger()

    def test(self, request):
        work_dir = self._create_temp_work_dir()
        new_path = self._save_user_file(request, work_dir)

        # Load problem config
        problem_directory = self.config['problem_directory']  # type: str
        if not problem_directory:
            raise errors.MissingConfigEntryError('problem_directory')

        # Check for full windows or *nix directory path
        if not (problem_directory.startswith('/') or ':' in problem_directory):
            # assume it's relative to the current working directory
            problem_directory = os.path.join(os.getcwd(), problem_directory)

        problem_config_path = os.path.join(
            problem_directory, '%s.yaml' % self.problem_id)
        problem_config = yaml.load(open(problem_config_path))

        result = ''
        for run in problem_config['runs']:
            program_input = run['input']
            expected = run['output']

            cmd_and_args = [self._get_compiler(), new_path]
            cmd_and_args.extend(program_input.split(' '))

            self.log.debug(cmd_and_args)
            output = check_output(
                cmd_and_args, cwd=work_dir, stderr=STDOUT, timeout=3)

            if output != expected:
                self.log.debug(
                    'output="{output}", expected="{expected}"'.format(
                        output=output, expected=expected
                    ))
                result = 'Invalid Output'
                break

        if work_dir:
            self._remove_temp_work_dir(work_dir)

        return result or 'success'

    @staticmethod
    def _save_user_file(request, work_dir):
        user_file = request.files[request.files.keys()[0]]
        new_path = os.path.join(work_dir, user_file.filename)
        user_file.save(new_path)
        return new_path

    def _create_temp_work_dir(self):
        base = self.config.get('work_directory')
        if not base:
            raise errors.MissingConfigEntryError('work_directory')

        working = True
        path = ''
        while working:
            path = base + os.sep + self._gen_random_string()

            if not os.path.exists(path):
                os.makedirs(path)
                working = False

        return path

    @staticmethod
    def _gen_random_string(length=20):
        return ''.join(choice(ascii_letters) for _ in range(length))

    @staticmethod
    def _remove_temp_work_dir(path):
        shutil.rmtree(path)

    def _get_lang(self, lang=None):
        lang = lang or self.lang
        mapped_lang = _lang_map.get(lang)
        self.log.debug('Mapped language {input} to {output}.'.format(
            input=lang, output=mapped_lang))
        return mapped_lang

    def _get_compiler(self, lang=None):
        if not lang:
            lang = self._get_lang()
        compiler = self.config.get('compilers', {}).get(lang)
        self.log.debug('Mapped {lang} to {compiler}.'.format(
            lang=lang, compiler=compiler
        ))
        return compiler
